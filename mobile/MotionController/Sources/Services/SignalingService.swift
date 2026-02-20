import Foundation
import Combine

protocol SignalingServiceDelegate: AnyObject {
    func signalingService(_ service: SignalingService, didReceiveMessage message: SignalingMessage)
    func signalingServiceDidConnect(_ service: SignalingService)
    func signalingServiceDidDisconnect(_ service: SignalingService)
}

final class SignalingService: NSObject, ObservableObject {
    weak var delegate: SignalingServiceDelegate?

    @Published var isConnected = false

    private var webSocketTask: URLSessionWebSocketTask?
    private var urlSession: URLSession?
    private var serverURL: URL?
    private var reconnectAttempts = 0
    private var shouldReconnect = false

    func connect(to url: URL) {
        serverURL = url
        shouldReconnect = true
        reconnectAttempts = 0
        establishConnection()
    }

    func disconnect() {
        shouldReconnect = false
        reconnectAttempts = 0
        webSocketTask?.cancel(with: .goingAway, reason: nil)
        webSocketTask = nil
        DispatchQueue.main.async {
            self.isConnected = false
        }
        delegate?.signalingServiceDidDisconnect(self)
    }

    func send(_ message: SignalingMessage) {
        guard let data = message.jsonData(),
              let string = String(data: data, encoding: .utf8) else { return }

        webSocketTask?.send(.string(string)) { error in
            if let error {
                print("[Signaling] Send error: \(error.localizedDescription)")
            }
        }
    }

    // MARK: - Private

    private func establishConnection() {
        guard let serverURL else { return }

        let session = URLSession(configuration: .default, delegate: self, delegateQueue: nil)
        self.urlSession = session
        let task = session.webSocketTask(with: serverURL)
        self.webSocketTask = task
        task.resume()
        receiveMessage()
    }

    private func receiveMessage() {
        webSocketTask?.receive { [weak self] result in
            guard let self else { return }

            switch result {
            case .success(let message):
                switch message {
                case .string(let text):
                    if let data = text.data(using: .utf8),
                       let signalingMessage = SignalingMessage.from(data: data) {
                        self.delegate?.signalingService(self, didReceiveMessage: signalingMessage)
                    }
                case .data(let data):
                    if let signalingMessage = SignalingMessage.from(data: data) {
                        self.delegate?.signalingService(self, didReceiveMessage: signalingMessage)
                    }
                @unknown default:
                    break
                }
                self.receiveMessage()

            case .failure(let error):
                print("[Signaling] Receive error: \(error.localizedDescription)")
                self.handleDisconnection()
            }
        }
    }

    private func handleDisconnection() {
        DispatchQueue.main.async {
            self.isConnected = false
        }
        delegate?.signalingServiceDidDisconnect(self)

        guard shouldReconnect,
              reconnectAttempts < Constants.Signaling.maxReconnectAttempts else {
            print("[Signaling] Max reconnect attempts reached")
            return
        }

        reconnectAttempts += 1
        print("[Signaling] Reconnecting (attempt \(reconnectAttempts)/\(Constants.Signaling.maxReconnectAttempts))...")

        DispatchQueue.global().asyncAfter(deadline: .now() + Constants.Signaling.reconnectDelay) { [weak self] in
            self?.establishConnection()
        }
    }
}

// MARK: - URLSessionWebSocketDelegate

extension SignalingService: URLSessionWebSocketDelegate {
    func urlSession(
        _ session: URLSession,
        webSocketTask: URLSessionWebSocketTask,
        didOpenWithProtocol protocol: String?
    ) {
        reconnectAttempts = 0
        DispatchQueue.main.async {
            self.isConnected = true
        }
        delegate?.signalingServiceDidConnect(self)
    }

    func urlSession(
        _ session: URLSession,
        webSocketTask: URLSessionWebSocketTask,
        didCloseWith closeCode: URLSessionWebSocketTask.CloseCode,
        reason: Data?
    ) {
        handleDisconnection()
    }
}
