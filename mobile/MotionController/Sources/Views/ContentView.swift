import SwiftUI

struct ContentView: View {
    @StateObject private var connectionVM = ConnectionViewModel()
    @StateObject private var controllerVM = ControllerViewModel()
    @State private var selectedTab = 0

    var body: some View {
        TabView(selection: $selectedTab) {
            NavigationView {
                if connectionVM.connectionState.isConnected {
                    ControllerView(
                        controllerVM: controllerVM,
                        onDisconnect: {
                            controllerVM.stopStreaming()
                            connectionVM.disconnect()
                        }
                    )
                } else {
                    ConnectionView(viewModel: connectionVM)
                }
            }
            .tabItem {
                Label("Controller", systemImage: "gamecontroller")
            }
            .tag(0)

            NavigationView {
                DebugView(
                    connectionVM: connectionVM,
                    controllerVM: controllerVM
                )
            }
            .tabItem {
                Label("Debug", systemImage: "ant")
            }
            .tag(1)
        }
        .onChange(of: connectionVM.connectionState) { newState in
            if newState.isConnected {
                controllerVM.bind(
                    signalingService: connectionVM.signalingService,
                    playerId: connectionVM.assignedPlayerId ?? 1
                )
                controllerVM.startStreaming()
            }
        }
        .onChange(of: connectionVM.assignedPlayerId) { newId in
            if let id = newId, connectionVM.connectionState.isConnected {
                controllerVM.bind(
                    signalingService: connectionVM.signalingService,
                    playerId: id
                )
            }
        }
    }
}
