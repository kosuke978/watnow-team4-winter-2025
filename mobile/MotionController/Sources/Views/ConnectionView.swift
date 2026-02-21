import SwiftUI

struct ConnectionView: View {
    @ObservedObject var viewModel: ConnectionViewModel

    private let bgYellow = Color(red: 240/255, green: 200/255, blue: 70/255)
    private let borderBrown = Color(red: 100/255, green: 25/255, blue: 25/255)

    var body: some View {
        GeometryReader { geo in
            ZStack {
                // TVフレーム（外枠）
                borderBrown.ignoresSafeArea()

                // 黄色の内側エリア
                bgYellow
                    .cornerRadius(4)
                    .padding(geo.size.height * 0.06)

                HStack(spacing: 0) {
                    // 左側: タイトル画像 + woman
                    ZStack(alignment: .bottomLeading) {
                        VStack {
                            Image("title")
                                .resizable()
                                .aspectRatio(contentMode: .fit)
                                .frame(maxWidth: geo.size.width * 0.45)
                            Spacer()
                        }

                        Image("woman")
                            .resizable()
                            .aspectRatio(contentMode: .fit)
                            .frame(width: geo.size.height * 0.25)
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)

                    // 右側: UFO + 名前入力 + STARTボタン
                    VStack(alignment: .trailing, spacing: 0) {
                        // UFO（右上）
                        Image("ufo")
                            .resizable()
                            .aspectRatio(contentMode: .fit)
                            .frame(height: geo.size.height * 0.22)

                        Spacer()

                        // 名前入力
                        VStack(alignment: .leading, spacing: 6) {
                            Text("名前を入力してね")
                                .font(.custom("DotGothic16-Regular", size: 14))
                                .foregroundColor(.black.opacity(0.7))

                            TextField("", text: $viewModel.playerName)
                                .placeholder(when: viewModel.playerName.isEmpty) {
                                    Text("なまえ")
                                        .font(.custom("DotGothic16-Regular", size: 16))
                                        .foregroundColor(.gray.opacity(0.5))
                                }
                                .font(.custom("DotGothic16-Regular", size: 16))
                                .foregroundColor(.black)
                                .padding(.horizontal, 14)
                                .padding(.vertical, 10)
                                .background(Color.white)
                                .cornerRadius(6)
                                .overlay(
                                    RoundedRectangle(cornerRadius: 6)
                                        .stroke(Color.gray.opacity(0.4), lineWidth: 1)
                                )
                                .autocapitalization(.none)
                                .disableAutocorrection(true)
                        }

                        // エラーメッセージ
                        if let error = viewModel.errorMessage {
                            Text(error)
                                .font(.custom("DotGothic16-Regular", size: 12))
                                .foregroundColor(.red)
                                .padding(.top, 4)
                        }

                        Spacer()

                        // STARTボタン
                        Button(action: {
                            viewModel.connect()
                        }) {
                            if viewModel.connectionState.isConnecting {
                                HStack(spacing: 8) {
                                    ProgressView()
                                        .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                    Text("接続中...")
                                        .font(.custom("DotGothic16-Regular", size: 16))
                                        .foregroundColor(.white)
                                }
                                .frame(width: geo.size.width * 0.22, height: geo.size.height * 0.22)
                                .background(borderBrown.opacity(0.7))
                                .cornerRadius(12)
                            } else {
                                Image("start")
                                    .resizable()
                                    .aspectRatio(contentMode: .fit)
                                    .frame(height: geo.size.height * 0.22)
                            }
                        }
                    }
                    .frame(width: geo.size.width * 0.38)
                }
                .padding(geo.size.height * 0.1)
            }
        }
        .navigationBarHidden(true)
    }
}

#Preview {
    ConnectionView(viewModel: ConnectionViewModel())
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
