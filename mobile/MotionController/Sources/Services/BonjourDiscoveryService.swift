import Foundation
import Network

@MainActor
final class BonjourDiscoveryService: ObservableObject {
    @Published var discoveredServer: String?
    @Published var isSearching = false

    private var browser: NWBrowser?
    private var resolveConnection: NWConnection?

    private let serviceType = "_ballgame._tcp"

    func start() {
        guard browser == nil else { return }

        let descriptor = NWBrowser.Descriptor.bonjour(type: serviceType, domain: nil)
        let params = NWParameters()
        params.includePeerToPeer = true

        let newBrowser = NWBrowser(for: descriptor, using: params)

        newBrowser.stateUpdateHandler = { [weak self] state in
            DispatchQueue.main.async {
                guard let self else { return }
                switch state {
                case .ready:
                    self.isSearching = true
                case .failed, .cancelled:
                    self.isSearching = false
                default:
                    break
                }
            }
        }

        newBrowser.browseResultsChangedHandler = { [weak self] results, _ in
            DispatchQueue.main.async {
                guard let self else { return }
                if let result = results.first {
                    self.resolve(result: result)
                } else {
                    self.discoveredServer = nil
                }
            }
        }

        newBrowser.start(queue: .main)
        browser = newBrowser
        isSearching = true
    }

    func stop() {
        browser?.cancel()
        browser = nil
        resolveConnection?.cancel()
        resolveConnection = nil
        isSearching = false
        discoveredServer = nil
    }

    // MARK: - Resolve endpoint to IP:port

    private func resolve(result: NWBrowser.Result) {
        resolveConnection?.cancel()

        let connection = NWConnection(to: result.endpoint, using: .tcp)

        connection.stateUpdateHandler = { [weak self] state in
            DispatchQueue.main.async {
                guard let self else { return }
                switch state {
                case .ready:
                    if let endpoint = connection.currentPath?.remoteEndpoint,
                       case let .hostPort(host, port) = endpoint {
                        let ip: String
                        switch host {
                        case .ipv4(let addr):
                            ip = "\(addr)"
                        case .ipv6(let addr):
                            ip = "\(addr)"
                        default:
                            ip = "\(host)"
                        }
                        self.discoveredServer = "ws://\(ip):\(port)/ws"
                    }
                    connection.cancel()
                case .failed, .cancelled:
                    break
                default:
                    break
                }
            }
        }

        connection.start(queue: .main)
        resolveConnection = connection
    }
}
