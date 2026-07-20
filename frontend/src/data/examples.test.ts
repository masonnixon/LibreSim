// Behavioral tests for example metadata and API-backed loading.
import { afterEach, expect, it, vi } from 'vitest'

import { api } from '../api/client'
import {
  clearExampleCache,
  exampleList,
  fetchExample,
  fetchExampleList,
  getExample,
} from './examples'

const caseFn = it
const cleanupFn = afterEach

cleanupFn(function () {
  clearExampleCache()
  vi.restoreAllMocks()
})

caseFn('returns the API example list', async function () {
  const expected = [{ id: 'sample', name: 'Sample', description: 'API', category: 'basic' }]
  vi.spyOn(api, 'getExampleList').mockResolvedValue(expected)
  await expect(fetchExampleList()).resolves.toEqual(expected)
})

caseFn('falls back to the embedded list when the API is unavailable', async function () {
  const failure = new Error('offline')
  vi.spyOn(api, 'getExampleList').mockRejectedValue(failure)
  const errorSpy = vi.spyOn(console, 'error').mockImplementation(function () {})

  const result = await fetchExampleList()

  expect(result).toBe(exampleList)
  expect(errorSpy).toHaveBeenCalledWith(
    'Failed to fetch example list from API, using fallback:',
    failure,
  )
})

caseFn('caches fetched models until the cache is cleared', async function () {
  const first = { id: 'cached-model' }
  const second = { id: 'refetched-model' }
  const getSpy = vi.spyOn(api, 'getExample')
    .mockResolvedValueOnce(first as never)
    .mockResolvedValueOnce(second as never)

  await expect(fetchExample('example-id')).resolves.toBe(first)
  await expect(fetchExample('example-id')).resolves.toBe(first)
  expect(getSpy).toHaveBeenCalledTimes(1)

  clearExampleCache()
  await expect(fetchExample('example-id')).resolves.toBe(second)
  expect(getSpy).toHaveBeenCalledTimes(2)
})

caseFn('returns undefined and reports an example fetch failure', async function () {
  const failure = new Error('missing example')
  vi.spyOn(api, 'getExample').mockRejectedValue(failure)
  const errorSpy = vi.spyOn(console, 'error').mockImplementation(function () {})

  await expect(fetchExample('missing-id')).resolves.toBeUndefined()
  expect(errorSpy).toHaveBeenCalledWith("Failed to fetch example 'missing-id':", failure)
})

caseFn('keeps the fallback catalog complete and internally consistent', function () {
  const ids = exampleList.map(function (example) { return example.id })
  const allowedCategories = new Set([
    'basic', 'control', 'signal', 'advanced', 'aerospace',
    'control_design', 'dsp', 'rf', 'navigation', 'sensor_fusion',
  ])

  expect(exampleList).toHaveLength(39)
  expect(new Set(ids).size).toBe(ids.length)
  for (const example of exampleList) {
    expect(example.id).not.toBe('')
    expect(example.name).not.toBe('')
    expect(example.description).not.toBe('')
    expect(allowedCategories.has(example.category)).toBe(true)
  }
})

caseFn('warns when the deprecated synchronous getter is used', function () {
  const warningSpy = vi.spyOn(console, 'warn').mockImplementation(function () {})

  expect(getExample('legacy-id')).toBeUndefined()
  expect(warningSpy).toHaveBeenCalledWith(
    'getExample is deprecated. Use fetchExample instead for async loading.',
  )
})
