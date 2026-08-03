import { fetchExample } from './data/examples'
import { useModelStore } from './store/modelStore'

export const EMBED_PARENT_ORIGIN = 'https://butterbot.tail7d452.ts.net:8934'

export interface StartupState {
  embed: boolean
  example?: string
  error?: string
}

export async function prepareStartup(search = window.location.search): Promise<StartupState> {
  const params = new URLSearchParams(search)
  const example = params.get('example') || undefined
  const embed = params.get('embed') === '1'

  if (!example) return { embed }

  const model = await fetchExample(example)
  if (!model) return { embed, example, error: `Example '${example}' could not be loaded.` }

  useModelStore.getState().loadModel(model)
  return { embed, example }
}

export function makeReadyNotifier(
  parentWindow: Pick<Window, 'postMessage'> = window.parent,
  currentWindow: Window = window,
) {
  let sent = false

  return (example?: string) => {
    if (!example || sent || parentWindow === currentWindow) return
    parentWindow.postMessage({ type: 'orbitlink:libresim-ready', example }, EMBED_PARENT_ORIGIN)
    sent = true
  }
}
