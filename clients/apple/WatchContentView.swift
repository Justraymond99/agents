import SwiftUI

struct WatchContentView: View {
    @StateObject private var client = AtlasAPIClient(
        baseURL: URL(string: "http://127.0.0.1:8000/")!
    )
    @State private var command = ""
    @State private var responseText = "Ready"

    var body: some View {
        NavigationStack {
            VStack(spacing: 8) {
                TextField("Ask ATLAS", text: $command)

                Button("Run") {
                    let goal = command.trimmingCharacters(in: .whitespacesAndNewlines)
                    guard !goal.isEmpty else { return }
                    Task {
                        do {
                            let result = try await client.submit(goal: goal)
                            responseText = "\(result.status)\n\(result.taskId.prefix(8))"
                        } catch {
                            responseText = "Error: \(error.localizedDescription)"
                        }
                    }
                }
                .buttonStyle(.borderedProminent)

                Text(responseText)
                    .font(.caption2)
                    .multilineTextAlignment(.center)
            }
            .navigationTitle("ATLAS")
        }
    }
}
