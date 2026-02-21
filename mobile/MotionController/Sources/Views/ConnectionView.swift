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

            HStack(spacing: 40) {
                // 左: タイトル
                titleSection

                // 右: 名前入力 + ステータス + 接続ボタン
                VStack(spacing: 16) {
                    nameField

                    statusBadge

                    if let error = viewModel.errorMessage {
                        Text(error)
                            .font(.custom("DotGothic16-Regular", size: 13))
                            .foregroundColor(.red)
                            .multilineTextAlignment(.center)
                    }

                    connectButton
                }
                .frame(maxWidth: 280)
            }
            .padding(.horizontal, 32)
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

    // MARK: - Name Field

    private var nameField: some View {
        TextField("", text: $viewModel.playerName)
            .placeholder(when: viewModel.playerName.isEmpty) {
                Text("なまえ")
                    .font(.custom("DotGothic16-Regular", size: 16))
                    .foregroundColor(subtextColor.opacity(0.5))
            }
            .font(.custom("DotGothic16-Regular", size: 16))
            .foregroundColor(.white)
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
            .background(
                RoundedRectangle(cornerRadius: 10)
                    .fill(Color.white.opacity(0.08))
            )
            .overlay(
                RoundedRectangle(cornerRadius: 10)
                    .stroke(accentGold.opacity(0.3), lineWidth: 1)
            )
            .autocapitalization(.none)
            .disableAutocorrection(true)
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
                .padding(.vertical, 14)
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

// MARK: - Placeholder modifier

extension View {
    func placeholder<Content: View>(
        when shouldShow: Bool,
        alignment: Alignment = .leading,
        @ViewBuilder placeholder: () -> Content
    ) -> some View {
        ZStack(alignment: alignment) {
            placeholder().opacity(shouldShow ? 1 : 0)
            self
        }
    }
}
