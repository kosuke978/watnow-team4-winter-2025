import SwiftUI

struct ConnectionView: View {
    @ObservedObject var viewModel: ConnectionViewModel

    var body: some View {
        VStack(spacing: 24) {
            statusIndicator

            discoveredServerSection

            serverURLInput

            connectButton

            if let error = viewModel.errorMessage {
                Text(error)
                    .font(.caption)
                    .foregroundColor(.red)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal)
            }

            recentServersList
        }
        .padding()
        .navigationTitle("Motion Controller")
    }

    // MARK: - Subviews

    private var discoveredServerSection: some View {
        Group {
            if let server = viewModel.discoveredServerURL {
                VStack(spacing: 8) {
                    HStack {
                        Image(systemName: "checkmark.circle.fill")
                            .foregroundColor(.green)
                        Text("サーバーが見つかりました")
                            .font(.subheadline)
                            .fontWeight(.medium)
                    }
                    Button(action: {
                        viewModel.connectToDiscovered()
                    }) {
                        HStack {
                            Image(systemName: "antenna.radiowaves.left.and.right")
                            Text(server)
                                .lineLimit(1)
                        }
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.green)
                        .foregroundColor(.white)
                        .cornerRadius(12)
                    }
                    .disabled(viewModel.connectionState.isConnecting)
                }
            } else if viewModel.isSearchingServer {
                HStack(spacing: 8) {
                    ProgressView()
                    Text("サーバーを検索中...")
                        .font(.subheadline)
                        .foregroundColor(.secondary)
                }
            }
        }
    }

    private var statusIndicator: some View {
        HStack {
            Circle()
                .fill(statusColor)
                .frame(width: 12, height: 12)
            Text(viewModel.connectionState.rawValue)
                .font(.subheadline)
                .foregroundColor(.secondary)
        }
        .padding(.vertical, 8)
    }

    private var serverURLInput: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Server URL")
                .font(.headline)

            TextField("ws://192.168.1.100:8080/ws", text: $viewModel.serverURLString)
                .textFieldStyle(.roundedBorder)
                .autocapitalization(.none)
                .disableAutocorrection(true)
                .keyboardType(.URL)
        }
    }

    private var connectButton: some View {
        Button(action: {
            if viewModel.connectionState.isConnecting {
                viewModel.disconnect()
            } else {
                viewModel.connect()
            }
        }) {
            Text(viewModel.connectionState.isConnecting ? "Cancel" : "Connect")
                .font(.headline)
                .frame(maxWidth: .infinity)
                .padding()
                .background(viewModel.connectionState.isConnecting ? Color.red : Color.blue)
                .foregroundColor(.white)
                .cornerRadius(12)
        }
        .disabled(viewModel.serverURLString.isEmpty)
    }

    private var recentServersList: some View {
        Group {
            if !viewModel.recentServers.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Recent Connections")
                        .font(.headline)

                    ForEach(viewModel.recentServers, id: \.self) { server in
                        Button(action: {
                            viewModel.selectRecentServer(server)
                        }) {
                            HStack {
                                Image(systemName: "clock")
                                    .foregroundColor(.secondary)
                                Text(server)
                                    .foregroundColor(.primary)
                                    .lineLimit(1)
                                Spacer()
                            }
                            .padding(.vertical, 4)
                        }
                    }
                }
            }
        }
    }

    private var statusColor: Color {
        switch viewModel.connectionState.statusColor {
        case "green": return .green
        case "orange": return .orange
        default: return .red
        }
    }
}
