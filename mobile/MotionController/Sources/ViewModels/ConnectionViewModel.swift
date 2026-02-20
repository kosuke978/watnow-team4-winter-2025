import Foundation
import Combine

@MainActor
final class ConnectionViewModel: ObservableObject {
    @Published var connectionState: ConnectionState = .disconnected
    @Published var serverURLString: String = ""
    @Published var recentServers: [String] = []
    @Published var errorMessage: String?
    @Published var discoveredServerURL: String?
    @Published var isSearchingServer = false

    let signalingService = SignalingService()
    let discoveryService = BonjourDiscoveryService()

    private var cancellables = Set<AnyCancellable>()

    init() {
        loadSavedData()
        signalingService.delegate = self
        observeDiscovery()
        discoveryService.start()
    }

    // MARK: - Public

    func connect() {
        guard let url = URL(string: serverURLString),
              serverURLString.hasPrefix("ws://") || serverURLString.hasPrefix("wss://") else {
            errorMessage = "Invalid URL. Use ws:// or wss:// prefix."
            return
        }

        errorMessage = nil
        connectionState = .connecting
        signalingService.connect(to: url)
        saveServer(serverURLString)
    }

    func disconnect() {
        signalingService.disconnect()
        connectionState = .disconnected
    }

    func selectRecentServer(_ server: String) {
        serverURLString = server
    }

    func connectToDiscovered() {
        guard let url = discoveredServerURL else { return }
        serverURLString = url
        connect()
    }

    // MARK: - Private

    private func observeDiscovery() {
        discoveryService.$discoveredServer
            .sink { [weak self] server in
                self?.discoveredServerURL = server
            }
            .store(in: &cancellables)
        discoveryService.$isSearching
            .sink { [weak self] searching in
                self?.isSearchingServer = searching
            }
            .store(in: &cancellables)
    }

    // MARK: - Persistence

    private func loadSavedData() {
        serverURLString = UserDefaults.standard.string(forKey: Constants.UserDefaultsKeys.serverURL)
            ?? "ws://192.168.1.100:8080/ws"
        recentServers = UserDefaults.standard.stringArray(forKey: Constants.UserDefaultsKeys.recentServers) ?? []
    }

    private func saveServer(_ server: String) {
        UserDefaults.standard.set(server, forKey: Constants.UserDefaultsKeys.serverURL)

        var servers = recentServers
        servers.removeAll { $0 == server }
        servers.insert(server, at: 0)
        if servers.count > 5 {
            servers = Array(servers.prefix(5))
        }
        recentServers = servers
        UserDefaults.standard.set(servers, forKey: Constants.UserDefaultsKeys.recentServers)
    }
}

// MARK: - SignalingServiceDelegate

extension ConnectionViewModel: SignalingServiceDelegate {
    nonisolated func signalingService(_ service: SignalingService, didReceiveMessage message: SignalingMessage) {
        // サーバーからのメッセージは無視（リレー専用）
    }

    nonisolated func signalingServiceDidConnect(_ service: SignalingService) {
        DispatchQueue.main.async {
            self.connectionState = .connected
            self.errorMessage = nil
        }
    }

    nonisolated func signalingServiceDidDisconnect(_ service: SignalingService) {
        DispatchQueue.main.async {
            if self.connectionState != .disconnected {
                self.connectionState = .failed
                self.errorMessage = "Server connection lost"
            }
        }
    }
}
