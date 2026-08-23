# ATLAS Apple client

This folder contains the initial Swift thin-client scaffold for iPhone/watchOS.

The Watch does **not** run the multi-agent harness. It sends commands to the ATLAS HTTP API and displays task status/results.

Current source files:

- `AtlasAPIClient.swift` — async HTTP client for task submission/status
- `WatchContentView.swift` — minimal watchOS command UI

## Next Xcode steps

1. Create an iOS app with a watchOS companion target.
2. Add these Swift files to the appropriate targets.
3. Replace the development base URL with the reachable ATLAS HTTPS endpoint.
4. Add authentication before exposing ATLAS outside a trusted development network.
5. Add WatchConnectivity/push notifications for completed tasks and approval prompts.
6. Add quick actions: Ask, Approve, Status, Save Memory.

Do not ship the current localhost URL or an unauthenticated public ATLAS endpoint.
