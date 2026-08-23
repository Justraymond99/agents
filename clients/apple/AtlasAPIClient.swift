import Foundation

struct AtlasTaskResponse: Decodable {
    let taskId: String
    let runId: String
    let status: String

    enum CodingKeys: String, CodingKey {
        case taskId = "task_id"
        case runId = "run_id"
        case status
    }
}

@MainActor
final class AtlasAPIClient: ObservableObject {
    @Published var lastStatus: String = "Idle"

    let baseURL: URL

    init(baseURL: URL) {
        self.baseURL = baseURL
    }

    func submit(goal: String) async throws -> AtlasTaskResponse {
        var request = URLRequest(url: baseURL.appending(path: "tasks"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONSerialization.data(withJSONObject: ["goal": goal])

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse, 200..<300 ~= http.statusCode else {
            throw URLError(.badServerResponse)
        }

        let result = try JSONDecoder().decode(AtlasTaskResponse.self, from: data)
        lastStatus = result.status
        return result
    }

    func taskStatus(taskId: String) async throws -> [String: Any] {
        let url = baseURL.appending(path: "tasks/\(taskId)")
        let (data, response) = try await URLSession.shared.data(from: url)
        guard let http = response as? HTTPURLResponse, 200..<300 ~= http.statusCode else {
            throw URLError(.badServerResponse)
        }
        return try JSONSerialization.jsonObject(with: data) as? [String: Any] ?? [:]
    }
}
