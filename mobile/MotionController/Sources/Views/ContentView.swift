import SwiftUI

struct ContentView: View {
    @StateObject private var connectionVM = ConnectionViewModel()
    @StateObject private var controllerVM = ControllerViewModel()

    var body: some View {
        NavigationView {
            if connectionVM.connectionState.isConnected {
                ControllerView(controllerVM: controllerVM)
            } else {
                ConnectionView(viewModel: connectionVM)
            }
        }
        .navigationViewStyle(.stack)
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

#Preview {
    ContentView()
}

