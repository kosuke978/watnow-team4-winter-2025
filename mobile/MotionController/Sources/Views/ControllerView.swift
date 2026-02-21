import SwiftUI

struct ControllerView: View {
    @ObservedObject var controllerVM: ControllerViewModel
    var onDisconnect: (() -> Void)?

    private let borderColor = Color(red: 100/255, green: 20/255, blue: 20/255)
    private let borderWidth: CGFloat = 18

    var body: some View {
        GeometryReader { geo in
            ZStack {
                // 外枠（マルーンボーダー）
                RoundedRectangle(cornerRadius: 16)
                    .fill(borderColor)
                    .ignoresSafeArea()

                // 内側の白エリア
                RoundedRectangle(cornerRadius: 8)
                    .fill(Color.white)
                    .padding(borderWidth)

                // コンテンツ
                VStack {
                    // 上部: ❌ボタン（左上）+ プレイヤーラベル（中央）
                    HStack {
                        Button(action: { onDisconnect?() }) {
                            Image(systemName: "xmark.circle.fill")
                                .font(.system(size: 28))
                                .foregroundColor(.gray)
                        }
                        Spacer()
                        playerLabel
                        Spacer()
                        // 左右バランス用の透明スペーサー
                        Color.clear.frame(width: 28, height: 28)
                    }
                    .padding(.top, borderWidth + 12)
                    .padding(.horizontal, borderWidth + 16)

                    Spacer()

                    // 下部: 戻るボタン（左）& 決定ボタン（右）
                    HStack {
                        // 戻るボタン（escape送信）
                        Button(action: { controllerVM.sendEscape() }) {
                            Image("yajirushi")
                                .resizable()
                                .aspectRatio(contentMode: .fit)
                                .frame(height: geo.size.height * 0.22)
                        }

                        Spacer()

                        // 決定ボタン（confirm送信）
                        Button(action: { controllerVM.sendConfirm() }) {
                            Image("button")
                                .resizable()
                                .aspectRatio(contentMode: .fit)
                                .frame(height: geo.size.height * 0.22)
                        }
                    }
                    .padding(.horizontal, borderWidth + 16)
                    .padding(.bottom, borderWidth + 12)
                }
            }
        }
        .navigationBarHidden(true)
    }

    // MARK: - プレイヤーラベル

    private var playerLabel: some View {
        let playerId = controllerVM.currentData?.playerId ?? 1

        return HStack(spacing: 12) {
            // キャラアイコン（1P: men, 2P: woman）
            Image(playerId == 1 ? "men" : "woman")
                .resizable()
                .interpolation(.none)
                .aspectRatio(contentMode: .fit)
                .frame(height: 40)

            Text("\(playerId)P")
                .font(.custom("DotGothic16-Regular", size: 32))
                .foregroundColor(.black)
        }
        .padding(.horizontal, 32)
        .padding(.vertical, 10)
        .background(
            RoundedRectangle(cornerRadius: 16)
                .fill(Color(white: 0.93))
                .overlay(
                    RoundedRectangle(cornerRadius: 16)
                        .stroke(Color.black, lineWidth: 2.5)
                )
        )
    }
}

#Preview {
    ControllerView(controllerVM: ControllerViewModel())
}
