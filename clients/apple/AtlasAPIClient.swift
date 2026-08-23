import Foundation

struct AtlasTaskResponse: Decodable {
    let taskId: String
    let status: String

    enum CodingKeys: String, CodingKey {
        case taskId = "id"
        case status
    }
}

@MainActor
final class AtlasAPIClient: ObservableObject {
    @Published var lastStatus: String = "Idle"

    let baseURL: URL
    let apiToken: String?

    init(baseURL: URL, apiToken: String? = nil) {
        self.baseURL = baseURL
        self.apiToken = apiToken
    }

    private func authorized(_ request: URLRequest) -> URLRequest {
        guard let apiToken, !apiToken.isEmpty else { return request }
        var copy = request
        copy.setValue("Bearer \(apiToken)", forHTTPHeaderField: "Authorization")
        return copy
    }

    func submit(goal: String) async throws -> AtlasTaskResponse {
        var request = URLRequest(url: baseURL.appending(path: "tasks"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONSerialization.data(withJSONObject: ["goal": goal])

        let (data, response) = try await URLSession.shared.data(for: authorized(request))
        guard let http = response as? HTTPURLResponse, 200..<300 ~= http.statusCode else {
            throw URLError(.badServerResponse)
        }

        let result = try JSONDecoder().decode(AtlasTaskResponse.self, from: data)
        lastStatus = result.status
        return result
    }

    func taskStatus(taskId: String) async throws -> [String: Any] {
        let url = baseURL.appending(path: "tasks/\(taskId)")
        let (data, response) = try await URLSession.shared.data(for: authorized(URLRequest(url: url)))
        guard let http = response as? HTTPURLResponse, 200..<300 ~= http.statusCode else {
            throw URLError(.badServerResponse)
        }
        return try JSONSerialization.jsonObject(with: data) as? [String: Any] ?? [:]
    }

    func taskResult(taskId: String) async throws -> [String: Any]? {
        let url = baseURL.appending(path: "tasks/\(taskId)/result")
        let (data, response) = try await URLSession.shared.data(for: authorized(URLRequest(url: url)))
        guard let http = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }
        if http.statusCode == 404 { return nil }
        guard 200..<300 ~= http.statusCode else { throw URLError(.badServerResponse) }
        return try JSONSerialization.jsonObject(with: data) as? [String: Any]
    }

    func resolveApproval(approvalId: String, approved: Bool) async throws {
        let url = baseURL.appending(path: "approvals/\(approvalId)/resolve")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONSerialization.data(withJSONObject: ["approved": approved])
        let (_, response) = try await URLSession.shared.data(for: authorized(request))
        guard let http = response as? HTTPURLResponse, 200..<300 ~= http.statusCode else {
            throw URLError(.badServerResponse)
        }
    }
}
