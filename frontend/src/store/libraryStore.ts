import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { nanoid } from '../utils/nanoid'
import type { BlockDefinition } from '../types/block'
import type {
  Library,
  LibraryBlockDefinition,
  LibraryImportResult,
  LibraryImportOptions,
  LibraryBlockImplementation,
} from '../types/library'

interface LibraryState {
  /** All imported libraries */
  libraries: Library[]

  /** Quick lookup map: libraryId -> Library */
  libraryMap: Map<string, Library>

  /** Quick lookup map: blockType -> LibraryBlockDefinition */
  libraryBlockMap: Map<string, LibraryBlockDefinition>

  // Actions
  /** Import a library from parsed data */
  importLibrary: (
    libraryData: Omit<Library, 'id' | 'importedAt'>,
    options?: LibraryImportOptions
  ) => LibraryImportResult

  /** Remove a library and all its block definitions */
  removeLibrary: (libraryId: string) => void

  /** Get a library by ID */
  getLibrary: (libraryId: string) => Library | undefined

  /** Get a library block definition by type */
  getLibraryBlock: (blockType: string) => LibraryBlockDefinition | undefined

  /** Get all blocks from a specific library */
  getLibraryBlocks: (libraryId: string) => LibraryBlockDefinition[]

  /** Get all library block definitions (for registry) */
  getAllLibraryBlocks: () => LibraryBlockDefinition[]

  /** Check if a block type is from a library */
  isLibraryBlock: (blockType: string) => boolean

  /** Get the implementation for a library block */
  getBlockImplementation: (blockType: string) => LibraryBlockImplementation | undefined

  /** Clear all libraries */
  clearAllLibraries: () => void

  /** Update internal maps after hydration */
  _rebuildMaps: () => void
}

export const useLibraryStore = create<LibraryState>()(
  persist(
    (set, get) => ({
      libraries: [],
      libraryMap: new Map(),
      libraryBlockMap: new Map(),

      importLibrary: (libraryData, options = {}) => {
        const { libraries, libraryMap } = get()
        const errors: string[] = []
        const warnings: string[] = []

        // Generate library ID and timestamp
        const libraryId = nanoid()
        const importedAt = new Date().toISOString()

        // Use provided name or keep the original
        const libraryName = options.name || libraryData.name

        // Check for existing library with same name
        const existingLibrary = libraries.find((lib) => lib.name === libraryName)
        if (existingLibrary && !options.replaceExisting) {
          errors.push(`Library "${libraryName}" already exists. Use replaceExisting option to overwrite.`)
          return { success: false, errors, warnings }
        }

        // Process blocks to add library metadata
        const processedBlocks: LibraryBlockDefinition[] = libraryData.blocks.map((block) => ({
          ...block,
          isLibraryBlock: true as const,
          libraryId,
          libraryName,
          // Generate unique type for this library block
          type: `${libraryName.toLowerCase().replace(/\s+/g, '_')}__${block.type}`,
          originalName: block.name,
        }))

        // Check for duplicate block types
        const existingTypes = new Set(get().libraryBlockMap.keys())
        processedBlocks.forEach((block) => {
          if (existingTypes.has(block.type) && !options.replaceExisting) {
            warnings.push(`Block type "${block.type}" already exists and will be skipped`)
          }
        })

        // Create the library object
        const library: Library = {
          id: libraryId,
          name: libraryName,
          description: libraryData.description,
          version: options.version || libraryData.version || '1.0.0',
          sourcePath: libraryData.sourcePath,
          sourceFormat: libraryData.sourceFormat,
          importedAt,
          blocks: processedBlocks,
        }

        // Remove existing library if replacing
        let updatedLibraries = libraries
        if (existingLibrary && options.replaceExisting) {
          updatedLibraries = libraries.filter((lib) => lib.id !== existingLibrary.id)
        }

        // Update state
        const newLibraries = [...updatedLibraries, library]
        const newLibraryMap = new Map(get().libraryMap)
        const newBlockMap = new Map(get().libraryBlockMap)

        // Remove old library from maps if replacing
        if (existingLibrary && options.replaceExisting) {
          newLibraryMap.delete(existingLibrary.id)
          existingLibrary.blocks.forEach((block) => {
            newBlockMap.delete(block.type)
          })
        }

        // Add new library to maps
        newLibraryMap.set(libraryId, library)
        processedBlocks.forEach((block) => {
          newBlockMap.set(block.type, block)
        })

        set({
          libraries: newLibraries,
          libraryMap: newLibraryMap,
          libraryBlockMap: newBlockMap,
        })

        return {
          success: true,
          library,
          errors,
          warnings,
        }
      },

      removeLibrary: (libraryId: string) => {
        const { libraries, libraryMap, libraryBlockMap } = get()
        const library = libraryMap.get(libraryId)
        if (!library) return

        // Remove from maps
        const newLibraryMap = new Map(libraryMap)
        const newBlockMap = new Map(libraryBlockMap)

        newLibraryMap.delete(libraryId)
        library.blocks.forEach((block) => {
          newBlockMap.delete(block.type)
        })

        set({
          libraries: libraries.filter((lib) => lib.id !== libraryId),
          libraryMap: newLibraryMap,
          libraryBlockMap: newBlockMap,
        })
      },

      getLibrary: (libraryId: string) => {
        return get().libraryMap.get(libraryId)
      },

      getLibraryBlock: (blockType: string) => {
        return get().libraryBlockMap.get(blockType)
      },

      getLibraryBlocks: (libraryId: string) => {
        const library = get().libraryMap.get(libraryId)
        return library ? library.blocks : []
      },

      getAllLibraryBlocks: () => {
        return Array.from(get().libraryBlockMap.values())
      },

      isLibraryBlock: (blockType: string) => {
        return get().libraryBlockMap.has(blockType)
      },

      getBlockImplementation: (blockType: string) => {
        const block = get().libraryBlockMap.get(blockType)
        return block?.implementation
      },

      clearAllLibraries: () => {
        set({
          libraries: [],
          libraryMap: new Map(),
          libraryBlockMap: new Map(),
        })
      },

      _rebuildMaps: () => {
        const { libraries } = get()
        const newLibraryMap = new Map<string, Library>()
        const newBlockMap = new Map<string, LibraryBlockDefinition>()

        libraries.forEach((library) => {
          newLibraryMap.set(library.id, library)
          library.blocks.forEach((block) => {
            newBlockMap.set(block.type, block)
          })
        })

        set({
          libraryMap: newLibraryMap,
          libraryBlockMap: newBlockMap,
        })
      },
    }),
    {
      name: 'libresim-libraries',
      // Only persist the libraries array, maps are rebuilt on hydration
      partialize: (state) => ({ libraries: state.libraries }),
      onRehydrateStorage: () => (state) => {
        // Rebuild maps after hydration from localStorage
        if (state) {
          state._rebuildMaps()
        }
      },
    }
  )
)

/**
 * Hook to get library blocks as BlockDefinition[] for the sidebar
 */
export function useLibraryBlockDefinitions(): BlockDefinition[] {
  const getAllLibraryBlocks = useLibraryStore((state) => state.getAllLibraryBlocks)
  return getAllLibraryBlocks()
}

/**
 * Hook to get all libraries
 */
export function useLibraries(): Library[] {
  return useLibraryStore((state) => state.libraries)
}
