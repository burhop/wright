# Editor host seams

Static inspection of the pinned source found an `IOProvider` interface, `BrowserIOProvider`, browser dataset persistence backed by IndexedDB, and `TauriNativeApi`. This establishes likely adapter points, not proof of workspace isolation. The persistence slice must inject a Wright workspace provider and prove two simultaneous workspaces cannot share file or dataset state.
