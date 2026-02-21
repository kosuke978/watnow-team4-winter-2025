import SwiftUI

struct ConnectionView: View {
    @ObservedObject var viewModel: ConnectionViewModel

    // デスクトップゲームのカラースキーム
    private let bgColor = Color(red: 30/255, green: 30/255, blue: 50/255)
    private let accentGold = Color(red: 245/255, green: 187/255, blue: 53/255)
    private let subtextColor = Color(red: 180/255, green: 180/255, blue: 180/255)

    var body: some View {
        ZStack {
            bgColor.ignoresSafeArea()

            VStack(spacing: 32) {
                Spacer()

                titleSection

                statusBadge

                if let error = viewModel.errorMessage {
                    Text(error)
                        .font(.custom("DotGothic16-Regular", size: 13))
                        .foregroundColor(.red)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal)
                }

                connectButton

                Spacer()
            }
            .padding(.horizontal, 24)
        }
        .navigationBarHidden(true)
    }

    // MARK: - Title

    private var titleSection: some View {
        VStack(spacing: 8) {
            Text("Motion Controller")
                .font(.custom("DotGothic16-Regular", size: 28))
                .foregroundColor(accentGold)

            Text("Ball Rolling Game")
                .font(.custom("DotGothic16-Regular", size: 14))
                .foregroundColor(subtextColor)
        }
    }

    // MARK: - Status Badge

    private var statusBadge: some View {
        HStack(spacing: 10) {
            Circle()
                .fill(statusColor)
                .frame(width: 10, height: 10)

            Text(viewModel.connectionState.rawValue)
                .font(.custom("DotGothic16-Regular", size: 14))
                .foregroundColor(.white)

            if let pid = viewModel.assignedPlayerId {
                Text("/ P\(pid)")
                    .font(.custom("DotGothic16-Regular", size: 14))
                    .foregroundColor(accentGold)
            }
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 10)
        .background(
            RoundedRectangle(cornerRadius: 20)
                .fill(Color.white.opacity(0.08))
        )
    }

    // MARK: - Connect Button

    private var connectButton: some View {
        Button(action: {
            if viewModel.connectionState.isConnecting {
                viewModel.disconnect()
            } else {
                viewModel.connect()
            }
        }) {
            Text(viewModel.connectionState.isConnecting ? "Cancel" : "Connect")
                .font(.custom("DotGothic16-Regular", size: 18))
                .frame(maxWidth: .infinity)
                .padding(.vertical, 16)
                .background(
                    viewModel.connectionState.isConnecting
                        ? Color.red.opacity(0.9)
                        : accentGold
                )
                .foregroundColor(viewModel.connectionState.isConnecting ? .white : bgColor)
                .cornerRadius(14)
        }
    }

    // MARK: - Helpers

    private var statusColor: Color {
        switch viewModel.connectionState.statusColor {
        case "green": return .green
        case "orange": return .orange
        default: return .red
        }
    }
}
