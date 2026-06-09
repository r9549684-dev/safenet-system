enum VpnStatus { disconnected, connecting, connected, disconnecting, error }

extension VpnStatusX on VpnStatus {
  bool get isActive => this == VpnStatus.connected;
  bool get isLoading => this == VpnStatus.connecting || this == VpnStatus.disconnecting;
  String get label {
    switch (this) {
      case VpnStatus.connected:     return 'Connected';
      case VpnStatus.connecting:    return 'Connecting...';
      case VpnStatus.disconnecting: return 'Disconnecting...';
      case VpnStatus.error:         return 'Error';
      default:                      return 'Connect';
    }
  }
}
