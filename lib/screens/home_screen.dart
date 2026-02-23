import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:intl/intl.dart';
import '../config/theme.dart';
import '../domain/enums/vpn_status.dart';
import '../domain/models/server.dart';
import '../providers/auth_provider.dart';
import '../providers/subscription_provider.dart';
import '../providers/vpn_provider.dart';
import '../data/local/secure_storage.dart';
import 'servers_screen.dart';
import 'splash_screen.dart';
import 'affiliate_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _tab = 0;
  String _mode = 'stealth';
  int _connectCount = 0;

  @override
  void initState() {
    super.initState();
    final vpn  = context.read<VpnProvider>();
    final auth = context.read<AuthProvider>();
    Future.microtask(() async {
      if (!mounted) return;
      await vpn.loadServers();
      if (!mounted) return;
      final hasFullAccess = (auth.user?.isPremium ?? false) || (auth.user?.isTrialActive ?? false);
      await vpn.checkAutoConnect(isPremium: hasFullAccess);
      // Тихая пред-регистрация — ускоряет первое подключение (цель — 5 секунд)
      if (!auth.isAuth) {
        final country = await SecureStorage.getCountry() ?? 'IR';
        try { await auth.register(country: country); } catch (_) {}
      }
    });
  }

  Future<void> _showPaymentSheet(BuildContext ctx) async {
    await showModalBottomSheet<void>(
      context: ctx,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => const _PaymentSheet(),
    );
  }

  @override
  void dispose() { super.dispose(); }

  @override
  Widget build(BuildContext context) {
    return Consumer<VpnProvider>(
      builder: (context, vpn, _) {
        final server = vpn.selected ?? vpn.active ?? VpnServer.defaults.first;
        return Scaffold(
          backgroundColor: AppTheme.bg,
          body: Stack(
            children: [
              // BG Orbs
              Positioned(top: -80, right: -80,
                child: Container(width: 256, height: 256,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: AppTheme.primary.withValues(alpha: 0.2),
                  ),
                ),
              ),
              Positioned(bottom: -80, left: -80,
                child: Container(width: 256, height: 256,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: AppTheme.success.withValues(alpha: 0.1),
                  ),
                ),
              ),
              // Content
              SafeArea(
                child: Column(
                  children: [
                    Expanded(
                      child: IndexedStack(
                        index: _tab,
                        children: [
                          _HomeTab(
                            status: vpn.status,
                            uptime: vpn.elapsedFormatted,
                            server: server,
                            mode: _mode,
                            error: vpn.error,
                            onUpgradeTap: () => setState(() => _tab = 2),
                            onToggle: () async {
                              if (vpn.status == VpnStatus.connected ||
                                  vpn.status == VpnStatus.error) {
                                if (vpn.status == VpnStatus.error) {
                                  final auth = context.read<AuthProvider>();
                                  final isPremium = (auth.user?.isPremium ?? false) || (auth.user?.isTrialActive ?? false);
                                  _connectCount++;
                                  if (!isPremium && _connectCount % 2 == 0 && mounted) {
                                    await _showPaymentSheet(context);
                                  }
                                  if (!mounted) return;
                                  vpn.connect(
                                    countryCode: server.country,
                                    mode: _mode,
                                    isPremium: isPremium,
                                  );
                                } else {
                                  vpn.disconnect();
                                }
                              } else if (vpn.status == VpnStatus.disconnected) {
                                final auth = context.read<AuthProvider>();
                                final isPremium = (auth.user?.isPremium ?? false) || (auth.user?.isTrialActive ?? false);
                                _connectCount++;
                                if (!isPremium && _connectCount % 2 == 0 && mounted) {
                                  await _showPaymentSheet(context);
                                }
                                if (!mounted) return;
                                vpn.connect(
                                  countryCode: server.country,
                                  mode: _mode,
                                  isPremium: isPremium,
                                );
                              }
                            },
                            onModeChange: (m) => setState(() => _mode = m),
                            onServerTap: () async {
                              final auth = context.read<AuthProvider>();
                              final hasFullAccess = (auth.user?.isPremium ?? false) || (auth.user?.isTrialActive ?? false);
                              if (!hasFullAccess && context.mounted) {
                                await _showPaymentSheet(context);
                              }
                              if (!context.mounted) return;
                              final s = await Navigator.push<VpnServer>(
                                context,
                                MaterialPageRoute(
                                  builder: (_) => ServersScreen(currentId: server.id),
                                ),
                              );
                              if (s != null) vpn.selectServer(s);
                            },
                          ),
                          ServersScreen(
                            currentId: server.id,
                            embedded: true,
                            onSelect: (s) {
                              vpn.selectServer(s);
                              setState(() => _tab = 0);
                            },
                          ),
                          const _PremiumTab(),
                          const _SettingsTab(),
                        ],
                      ),
                    ),
                    _BottomNav(current: _tab, onTap: (i) => setState(() => _tab = i)),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

// ── Home Tab ─────────────────────────────────────────────────────────────────
class _HomeTab extends StatelessWidget {
  final VpnStatus status;
  final String uptime;
  final VpnServer server;
  final String mode;
  final String? error;
  final VoidCallback onToggle;
  final ValueChanged<String> onModeChange;
  final VoidCallback onServerTap;
  final VoidCallback onUpgradeTap;

  const _HomeTab({
    required this.status, required this.uptime, required this.server,
    required this.mode, this.error, required this.onToggle,
    required this.onModeChange, required this.onServerTap,
    required this.onUpgradeTap,
  });

  Color get _btnColor {
    switch (status) {
      case VpnStatus.connected:      return AppTheme.success;
      case VpnStatus.connecting:
      case VpnStatus.disconnecting:  return AppTheme.warning;
      case VpnStatus.error:          return AppTheme.error;
      default:                       return AppTheme.surface;
    }
  }

  Color get _btnBorder {
    switch (status) {
      case VpnStatus.connected:     return const Color(0xFF34D399);
      case VpnStatus.connecting:
      case VpnStatus.disconnecting: return const Color(0xFFFBBF24);
      case VpnStatus.error:         return AppTheme.error;
      default:                      return AppTheme.primary;
    }
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                const Text('SAFENET',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900,
                    fontStyle: FontStyle.italic, letterSpacing: -0.5, color: AppTheme.textPrimary)),
                Row(children: [
                  AnimatedContainer(
                    duration: const Duration(milliseconds: 500),
                    width: 8, height: 8,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: status == VpnStatus.connected ? AppTheme.success : AppTheme.textMuted,
                      boxShadow: status == VpnStatus.connected
                        ? [BoxShadow(color: AppTheme.success.withValues(alpha: 0.6), blurRadius: 8)]
                        : null,
                    ),
                  ),
                  const SizedBox(width: 6),
                  Text(
                    status == VpnStatus.connected ? 'Secure Tunnel Active' : 'Offline',
                    style: const TextStyle(fontSize: 10, color: AppTheme.textMuted,
                      fontWeight: FontWeight.w700, letterSpacing: 2),
                  ),
                ]),
              ]),
              Consumer<AuthProvider>(
                builder: (ctx, auth, _) {
                  final user = auth.user;
                  final label = user == null
                      ? ''
                      : user.isPremium
                          ? 'PREMIUM ✓'
                          : 'ТРИАЛ: ${user.trialDaysLeft} ДНЕЙ';
                  if (label.isEmpty) return const SizedBox.shrink();
                  return Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(colors: [Color(0xFFF59E0B), Color(0xFFF97316)]),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(label,
                      style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: Colors.white)),
                  );
                },
              ),
            ],
          ),

          const SizedBox(height: 32),

          // Connect Button
          Center(
            child: SizedBox(
              height: 220,
              child: Stack(
                alignment: Alignment.center,
                children: [
                  AnimatedContainer(
                    duration: const Duration(milliseconds: 800),
                    width: 220, height: 220,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: _btnColor.withValues(alpha: 0.15),
                    ),
                  ),
                  GestureDetector(
                    onTap: onToggle,
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 500),
                      width: 180, height: 180,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: _btnColor,
                        border: Border.all(color: _btnBorder, width: 4),
                        boxShadow: [BoxShadow(color: _btnColor.withValues(alpha: 0.4), blurRadius: 40)],
                      ),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          if (status == VpnStatus.connecting || status == VpnStatus.disconnecting)
                            const SizedBox(width: 40, height: 40,
                              child: CircularProgressIndicator(color: Colors.white, strokeWidth: 3))
                          else
                            Icon(
                              status == VpnStatus.connected
                                ? Icons.lock_rounded
                                : status == VpnStatus.error
                                  ? Icons.error_rounded
                                  : Icons.lock_open_rounded,
                              size: 48,
                              color: status == VpnStatus.disconnected ? AppTheme.primary : Colors.white,
                            ),
                          const SizedBox(height: 8),
                          Text(
                            status == VpnStatus.connected ? 'DISCONNECT'
                            : status == VpnStatus.connecting ? 'CONNECTING'
                            : status == VpnStatus.disconnecting ? 'STOPPING'
                            : status == VpnStatus.error ? 'RETRY'
                            : 'CONNECT',
                            style: TextStyle(
                              fontSize: 13, fontWeight: FontWeight.w900, letterSpacing: 2,
                              color: status == VpnStatus.disconnected ? AppTheme.primary : Colors.white,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),

          if (status == VpnStatus.connected) ...[
            Center(
              child: Text(uptime,
                style: const TextStyle(fontFamily: 'monospace', fontSize: 20,
                  color: AppTheme.success, letterSpacing: 4)),
            ),
            const SizedBox(height: 4),
            const Center(
              child: Text('Secure Tunnel Active',
                style: TextStyle(fontSize: 11, color: AppTheme.success,
                  fontWeight: FontWeight.w700, letterSpacing: 2)),
            ),
            const SizedBox(height: 12),
          ],
          if (status == VpnStatus.error && error != null) ...[
            Center(
              child: Container(
                margin: const EdgeInsets.symmetric(horizontal: 8),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppTheme.error.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppTheme.error.withValues(alpha: 0.3)),
                ),
                child: Column(children: [
                  Text(
                    error!,
                    style: const TextStyle(fontSize: 11, color: AppTheme.error),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 10),
                  GestureDetector(
                    onTap: onUpgradeTap,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          colors: [Color(0xFFF59E0B), Color(0xFFF97316)]),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: const Text('💎 Убрать ограничение — Premium',
                        style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: Colors.white)),
                    ),
                  ),
                ]),
              ),
            ),
            const SizedBox(height: 12),
          ],

          const SizedBox(height: 16),

          // Server Card
          GestureDetector(
            onTap: onServerTap,
            child: _GlassCard(
              child: Row(
                children: [
                  Text(server.flag, style: const TextStyle(fontSize: 36)),
                  const SizedBox(width: 14),
                  Expanded(child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(server.country, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 15)),
                    Text('${server.cityLabel} • ${server.ping}ms',
                        style: const TextStyle(fontSize: 11, color: AppTheme.textMuted)),
                    ],
                  )),
                  _ModeBadge(server.mode),
                  const SizedBox(width: 8),
                  const Icon(Icons.chevron_right, color: AppTheme.textMuted),
                ],
              ),
            ),
          ),

          const SizedBox(height: 20),

          // Bypass Modes
          const Text('РЕЖИМ ОБХОДА',
            style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700,
              color: AppTheme.textMuted, letterSpacing: 3)),
          const SizedBox(height: 10),
          GridView.count(
            crossAxisCount: 2, shrinkWrap: true, physics: const NeverScrollableScrollPhysics(),
            crossAxisSpacing: 10, mainAxisSpacing: 10, childAspectRatio: 2.2,
            children: [
              _ModeCard(id: 'stealth', label: 'Stealth', desc: 'Авто-выбор',
                icon: Icons.shield_rounded, selected: mode == 'stealth', onTap: onModeChange),
              _ModeCard(id: 'byedpi', label: 'ByeDPI', desc: 'Обход DPI',
                icon: Icons.bolt_rounded, selected: mode == 'byedpi', onTap: onModeChange),
              _ModeCard(id: 'amnezia', label: 'AmneziaWG', desc: 'WireGuard+',
                icon: Icons.lock_rounded, selected: mode == 'amnezia', onTap: onModeChange),
              _ModeCard(id: 'hybrid', label: 'Hybrid', desc: 'Комбо',
                icon: Icons.grid_view_rounded, selected: mode == 'hybrid', onTap: onModeChange),
            ],
          ),

          if (status == VpnStatus.connected) ...[
            const SizedBox(height: 20),
            Consumer<VpnProvider>(
              builder: (ctx, vpn, _) => Row(children: [
                _StatCard(label: 'Загрузка', value: vpn.rxSpeedFormatted, color: AppTheme.success),
                const SizedBox(width: 10),
                _StatCard(label: 'Отдача',   value: vpn.txSpeedFormatted, color: AppTheme.primary),
                const SizedBox(width: 10),
                _StatCard(label: 'Пинг',     value: '${server.ping}ms',   color: AppTheme.warning),
              ]),
            ),
          ],

          // Trial upgrade banner (only for non-premium)
          Consumer<AuthProvider>(
            builder: (ctx, auth, _) {
              final user = auth.user;
              if (user == null || user.isPremium) return const SizedBox.shrink();
              final days = user.trialDaysLeft;
              final urgency = days <= 1
                  ? '🔴 Последний день триала!'
                  : days <= 3
                      ? '🟡 Осталось $days дня триала'
                      : '⏳ Триал: $days дней';
              return Padding(
                padding: const EdgeInsets.only(top: 16),
                child: GestureDetector(
                  onTap: onUpgradeTap,
                  child: Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: [
                          const Color(0xFFF59E0B).withValues(alpha: 0.15),
                          const Color(0xFFF97316).withValues(alpha: 0.15),
                        ],
                      ),
                      border: Border.all(color: const Color(0xFFF59E0B).withValues(alpha: 0.4)),
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: Row(
                      children: [
                        const Text('💎', style: TextStyle(fontSize: 28)),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(urgency,
                                style: const TextStyle(
                                  fontSize: 12, fontWeight: FontWeight.w800,
                                  color: Color(0xFFF59E0B))),
                              const SizedBox(height: 2),
                              Text(
                                days > 0
                                  ? 'Во время триала: безлимит как Premium'
                                  : 'После триала: сессии по 5 минут',
                                style: const TextStyle(fontSize: 10, color: AppTheme.textMuted),
                              ),
                              const SizedBox(height: 6),
                              const Text(
                                'Перейти на Premium →',
                                style: TextStyle(
                                  fontSize: 11, fontWeight: FontWeight.w800,
                                  color: Color(0xFFF97316))),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              );
            },
          ),

          const SizedBox(height: 20),
        ],
      ),
    );
  }
}

// ── Premium Tab ───────────────────────────────────────────────────────────────
class _PremiumTab extends StatefulWidget {
  const _PremiumTab();
  @override
  State<_PremiumTab> createState() => _PremiumTabState();
}

class _PremiumTabState extends State<_PremiumTab> {
  String _selected = 'quarterly';

  final _plans = [
    {'id': 'monthly', 'label': '1 Месяц', 'price': '5.99', 'popular': false, 'save': null},
    {'id': 'quarterly', 'label': '3 Месяца', 'price': '14.99', 'popular': true, 'save': '17%'},
    {'id': 'yearly', 'label': '12 Месяцев', 'price': '29.99', 'popular': false, 'save': '37%'},
  ];

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 0),
      child: Column(
        children: [
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFFF59E0B), Color(0xFFF97316)],
                begin: Alignment.topLeft, end: Alignment.bottomRight),
              borderRadius: BorderRadius.circular(24),
              boxShadow: [BoxShadow(
                color: const Color(0xFFF59E0B).withValues(alpha: 0.3),
                blurRadius: 24, offset: const Offset(0, 8))],
            ),
            child: const Icon(Icons.diamond_rounded, size: 52, color: Colors.white),
          ),
          const SizedBox(height: 16),
          const Text('SafeNet Premium',
            style: TextStyle(fontSize: 28, fontWeight: FontWeight.w900, color: AppTheme.textPrimary)),
          const SizedBox(height: 4),
          const Text('Безлимитный доступ ко всем технологиям',
            style: TextStyle(fontSize: 14, color: AppTheme.textSecondary)),
          const SizedBox(height: 20),

          // Feature comparison
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppTheme.surface,
              border: Border.all(color: AppTheme.border),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Column(children: [
              // Column headers
              const Row(children: [
                Expanded(flex: 5, child: SizedBox()),
                Expanded(flex: 3,
                  child: Center(
                    child: Text('ТРИАЛ',
                      style: TextStyle(fontSize: 9, fontWeight: FontWeight.w800,
                        color: AppTheme.textMuted, letterSpacing: 2)))),
                Expanded(flex: 3,
                  child: Center(
                    child: Text('PREMIUM',
                      style: TextStyle(fontSize: 9, fontWeight: FontWeight.w800,
                        color: AppTheme.success, letterSpacing: 2)))),
              ]),
              const Divider(color: AppTheme.border, height: 16, thickness: 0.5),
              const _FeatureRow('Длительность сессии', trial: '3 дня безлимит', premium: 'Безлимит ♾'),
              _featureDivider(),
              const _FeatureRow('Авто-подключение', trial: '✓ (3 дня)', premium: '✓'),
              _featureDivider(),
              const _FeatureRow('Kill Switch', trial: '✓', premium: '✓'),
              _featureDivider(),
              const _FeatureRow('Режимы обхода', trial: 'Все 4', premium: 'Все 4'),
              _featureDivider(),
              const _FeatureRow('Серверы', trial: 'Базовые', premium: 'Все страны'),
              _featureDivider(),
              const _FeatureRow('Приоритет поддержки', trial: '✗', premium: '✓'),
            ]),
          ),
          const SizedBox(height: 20),

          // Social proof
          Consumer<AuthProvider>(
            builder: (ctx, auth, _) {
              final user = auth.user;
              if (user == null || user.isPremium) return const SizedBox.shrink();
              final days = user.trialDaysLeft;
              return Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                decoration: BoxDecoration(
                  color: AppTheme.error.withValues(alpha: 0.08),
                  border: Border.all(color: AppTheme.error.withValues(alpha: 0.25)),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(children: [
                  const Text('⚠️', style: TextStyle(fontSize: 18)),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      days <= 0
                        ? 'Триал истёк — доступны сессии по 5 минут.'
                        : 'Триал заканчивается через $days ${_daysWord(days)}. Пока действует — полный Premium.',
                      style: const TextStyle(
                        fontSize: 12, fontWeight: FontWeight.w700, color: AppTheme.error),
                    ),
                  ),
                ]),
              );
            },
          ),
          const SizedBox(height: 20),

          // Plan selection label
          const Align(
            alignment: Alignment.centerLeft,
            child: Text('ВЫБЕРИТЕ ПЛАН',
              style: TextStyle(fontSize: 10, fontWeight: FontWeight.w800,
                color: AppTheme.textMuted, letterSpacing: 3)),
          ),
          const SizedBox(height: 12),

          ..._plans.map((p) => Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: GestureDetector(
              onTap: () => setState(() => _selected = p['id'] as String),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                padding: const EdgeInsets.all(20),
                decoration: BoxDecoration(
                  color: _selected == p['id'] ? AppTheme.primary.withValues(alpha: 0.1) : AppTheme.surface,
                  border: Border.all(
                    color: _selected == p['id'] ? AppTheme.primary : Colors.transparent,
                    width: 2,
                  ),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Row(
                  children: [
                    Expanded(child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(children: [
                          Text(p['label'] as String,
                            style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w900)),
                          if (p['popular'] == true) ...[
                            const SizedBox(width: 8),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                              decoration: BoxDecoration(
                                gradient: const LinearGradient(
                                  colors: [Color(0xFFF59E0B), Color(0xFFF97316)]),
                                borderRadius: BorderRadius.circular(6),
                              ),
                              child: const Text('🔥 ЛУЧШАЯ ЦЕНА',
                                style: TextStyle(fontSize: 9, fontWeight: FontWeight.w700, color: Colors.white)),
                            ),
                          ],
                        ]),
                        if (p['save'] != null)
                          Text('Экономия ${p['save']}',
                            style: const TextStyle(fontSize: 11, color: AppTheme.success, fontWeight: FontWeight.w700)),
                      ],
                    )),
                    Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
                      Text('\$${p['price']}',
                        style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w900)),
                      const Text('USDT / TON',
                        style: TextStyle(fontSize: 9, color: AppTheme.textMuted,
                          fontWeight: FontWeight.w700, letterSpacing: 2)),
                    ]),
                  ],
                ),
              ),
            ),
          )),
          const SizedBox(height: 8),
          Consumer<SubscriptionProvider>(
            builder: (ctx, sub, _) {
              return SizedBox(
                width: double.infinity,
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(colors: [Color(0xFF4F46E5), Color(0xFF7C3AED)]),
                    borderRadius: BorderRadius.circular(16),
                    boxShadow: [BoxShadow(color: AppTheme.primary.withValues(alpha: 0.3), blurRadius: 24, offset: const Offset(0, 8))],
                  ),
                  child: ElevatedButton(
                    onPressed: sub.isLoading ? null : () async {
                      final url = await sub.createPurchase(_selected);
                      if (url != null && ctx.mounted) {
                        final uri = Uri.tryParse(url);
                        if (uri != null && await canLaunchUrl(uri)) {
                          await launchUrl(uri, mode: LaunchMode.externalApplication);
                        }
                      } else if (sub.error != null && ctx.mounted) {
                        ScaffoldMessenger.of(ctx).showSnackBar(
                          SnackBar(content: Text(sub.error!), backgroundColor: AppTheme.error),
                        );
                      }
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.transparent, shadowColor: Colors.transparent,
                      padding: const EdgeInsets.symmetric(vertical: 18),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                    ),
                    child: sub.isLoading
                        ? const SizedBox(width: 24, height: 24,
                            child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                        : const Text('Оплатить в CryptoBot',
                            style: TextStyle(fontSize: 17, fontWeight: FontWeight.w900, color: Colors.white)),
                  ),
                ),
              );
            },
          ),
          const SizedBox(height: 12),
          const Text('БЕЗОПАСНАЯ ОПЛАТА • АКТИВАЦИЯ МГНОВЕННО',
            style: TextStyle(fontSize: 10, color: AppTheme.textMuted,
              fontWeight: FontWeight.w700, letterSpacing: 2)),
          const SizedBox(height: 4),
          const Text('Оплата в USDT / TON через CryptoBot',
            style: TextStyle(fontSize: 10, color: AppTheme.textMuted, letterSpacing: 1)),
          const SizedBox(height: 20),
        ],
      ),
    );
  }

  static String _daysWord(int days) {
    if (days == 1) return 'день';
    if (days >= 2 && days <= 4) return 'дня';
    return 'дней';
  }

  static Widget _featureDivider() =>
    const Divider(color: AppTheme.border, height: 12, thickness: 0.5);
}

class _FeatureRow extends StatelessWidget {
  final String feature;
  final String trial;
  final String premium;
  const _FeatureRow(this.feature, {required this.trial, required this.premium});

  @override
  Widget build(BuildContext context) {
    final trialPositive = trial == '✓' || trial.startsWith('Все') || trial.startsWith('Баз');
    final premiumPositive = premium != '✗';
    return Row(children: [
      Expanded(
        flex: 5,
        child: Text(feature,
          style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600,
            color: AppTheme.textSecondary)),
      ),
      Expanded(
        flex: 3,
        child: Center(
          child: Text(trial,
            style: TextStyle(
              fontSize: 11, fontWeight: FontWeight.w700,
              color: trialPositive ? AppTheme.textSecondary : AppTheme.error)),
        ),
      ),
      Expanded(
        flex: 3,
        child: Center(
          child: Text(premium,
            style: TextStyle(
              fontSize: 11, fontWeight: FontWeight.w800,
              color: premiumPositive ? AppTheme.success : AppTheme.error)),
        ),
      ),
    ]);
  }
}

// ── Settings Tab ──────────────────────────────────────────────────────────────
class _SettingsTab extends StatefulWidget {
  const _SettingsTab();
  @override
  State<_SettingsTab> createState() => _SettingsTabState();
}

class _SettingsTabState extends State<_SettingsTab> {
  bool _killSwitch  = true;
  bool _autoConnect = false;

  @override
  void initState() {
    super.initState();
    _loadPrefs();
  }

  Future<void> _loadPrefs() async {
    final ks = await SecureStorage.getKillSwitch();
    final ac = await SecureStorage.getAutoConnect();
    if (mounted) setState(() { _killSwitch = ks; _autoConnect = ac; });
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<AuthProvider>(
      builder: (ctx, auth, _) {
        final user = auth.user;
        final deviceId  = user?.deviceId ?? '—';
        final shortId   = deviceId.length > 8
            ? '${deviceId.substring(0, 4)}...${deviceId.substring(deviceId.length - 4)}'
            : deviceId;
        final expiryStr = user?.trialEndsAt != null
            ? DateFormat('d MMM yyyy, HH:mm', 'ru').format(user!.trialEndsAt!)
            : '—';
        final badgeLabel = (user?.isPremium ?? false) ? 'PREMIUM' : 'TRIAL';

        return SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(20, 20, 20, 0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Настройки',
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900, color: AppTheme.textPrimary)),
              const SizedBox(height: 24),
              _sectionLabel('Аккаунт'),
              _GlassCard(
                padding: EdgeInsets.zero,
                child: Column(children: [
                  _SettingsRow(
                    icon: '🛡️', title: 'ID Устройства', subtitle: shortId,
                    trailing: _badge(badgeLabel, AppTheme.warning),
                  ),
                  const Divider(color: AppTheme.border, height: 1),
                  _SettingsRow(
                    icon: '⏰', title: 'Истекает',
                    trailing: Text(expiryStr,
                      style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppTheme.textSecondary)),
                  ),
                ]),
              ),
              const SizedBox(height: 24),
              _sectionLabel('VPN Параметры'),
              _GlassCard(
                padding: EdgeInsets.zero,
                child: Column(children: [
                  _SettingsRow(
                    icon: '⚠️', title: 'Kill Switch',
                    subtitle: 'Твой IP не засветится при обрыве',
                    trailing: _Toggle(
                      value: _killSwitch,
                      onChanged: (v) async {
                        setState(() => _killSwitch = v);
                        await SecureStorage.saveKillSwitch(v);
                      },
                    ),
                  ),
                  const Divider(color: AppTheme.border, height: 1),
                  _SettingsRow(
                    icon: '⚡', title: 'Авто-подключение',
                    subtitle: 'При запуске приложения',
                    trailing: _Toggle(
                      value: _autoConnect,
                      onChanged: (v) async {
                        setState(() => _autoConnect = v);
                        await SecureStorage.saveAutoConnect(v);
                      },
                    ),
                  ),
                ]),
              ),
              const SizedBox(height: 32),
              SizedBox(
                width: double.infinity,
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    color: AppTheme.error.withValues(alpha: 0.12),
                    border: Border.all(color: AppTheme.error.withValues(alpha: 0.35)),
                    borderRadius: BorderRadius.circular(14),
                  ),
                  child: ElevatedButton.icon(
                    icon: const Icon(Icons.restart_alt_rounded, color: AppTheme.error),
                    label: const Text(
                      'Вернуться к первоначальным настройкам',
                      style: TextStyle(
                        color: AppTheme.error,
                        fontSize: 14,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                    onPressed: () async {
                      final confirmed = await showDialog<bool>(
                        context: ctx,
                        builder: (d) => AlertDialog(
                          backgroundColor: AppTheme.surface,
                          title: const Text('Начнём сначала?',
                            style: TextStyle(color: AppTheme.textPrimary)),
                          content: const Text(
                            'Все начнется заново.',
                            style: TextStyle(color: AppTheme.textSecondary),
                          ),
                          actions: [
                            TextButton(
                              onPressed: () => Navigator.pop(d, false),
                              child: const Text('Отмена'),
                            ),
                            TextButton(
                              onPressed: () => Navigator.pop(d, true),
                              child: const Text(
                                'Подтвердить',
                                style: TextStyle(color: AppTheme.error),
                              ),
                            ),
                          ],
                        ),
                      );
                      if (confirmed == true && ctx.mounted) {
                        await ctx.read<AuthProvider>().logout();
                        if (ctx.mounted) {
                          Navigator.of(ctx).pushAndRemoveUntil(
                            MaterialPageRoute(builder: (_) => const SplashScreen()),
                            (route) => false,
                          );
                        }
                      }
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.transparent,
                      shadowColor: Colors.transparent,
                      elevation: 0,
                      padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 12),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 20),
              _GlassCard(
                padding: EdgeInsets.zero,
                child: ListTile(
                  leading: const Text('🤝', style: TextStyle(fontSize: 20)),
                  title: const Text('Партнёрская программа',
                    style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: AppTheme.textPrimary)),
                  subtitle: const Text('Зарабатывай на рефералах',
                    style: TextStyle(fontSize: 11, color: AppTheme.textMuted)),
                  trailing: const Icon(Icons.arrow_forward_ios_rounded, size: 14, color: AppTheme.textMuted),
                  onTap: () => Navigator.push(
                    ctx,
                    MaterialPageRoute(builder: (_) => const AffiliateScreen()),
                  ),
                ),
              ),
              const SizedBox(height: 20),
            ],
          ),
        );
      },
    );
  }

  Widget _sectionLabel(String text) => Padding(
    padding: const EdgeInsets.only(bottom: 10),
    child: Text(text.toUpperCase(),
      style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w700,
        color: AppTheme.textMuted, letterSpacing: 3)),
  );

  Widget _badge(String text, Color color) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
    decoration: BoxDecoration(
      color: color.withValues(alpha: 0.2),
      border: Border.all(color: color.withValues(alpha: 0.3)),
      borderRadius: BorderRadius.circular(6),
    ),
    child: Text(text, style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: color)),
  );
}

// ── Bottom Nav ────────────────────────────────────────────────────────────────
class _BottomNav extends StatelessWidget {
  final int current;
  final ValueChanged<int> onTap;
  const _BottomNav({required this.current, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final items = [
      {'icon': Icons.bolt_rounded, 'label': 'Главная'},
      {'icon': Icons.language_rounded, 'label': 'Серверы'},
      {'icon': Icons.diamond_rounded, 'label': 'Премиум'},
      {'icon': Icons.settings_rounded, 'label': 'Опции'},
    ];
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(32),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
            decoration: BoxDecoration(
              color: AppTheme.surface.withValues(alpha: 0.85),
              border: Border.all(color: AppTheme.border),
              borderRadius: BorderRadius.circular(32),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: List.generate(items.length, (i) {
                final isActive = current == i;
                return GestureDetector(
                  onTap: () => onTap(i),
                  child: AnimatedScale(
                    scale: isActive ? 1.1 : 1.0,
                    duration: const Duration(milliseconds: 200),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(items[i]['icon'] as IconData,
                          size: 24,
                          color: isActive ? AppTheme.primary : AppTheme.textMuted,
                        ),
                        const SizedBox(height: 3),
                        Text((items[i]['label'] as String).toUpperCase(),
                          style: TextStyle(
                            fontSize: 9, fontWeight: FontWeight.w700, letterSpacing: 0.5,
                            color: isActive ? AppTheme.primary : AppTheme.textMuted,
                          )),
                      ],
                    ),
                  ),
                );
              }),
            ),
          ),
        ),
      ),
    );
  }
}

// ── Helper Widgets ─────────────────────────────────────────────────────────────

class _GlassCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry? padding;
  const _GlassCard({required this.child, this.padding});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: padding ?? const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.surface,
        border: Border.all(color: AppTheme.border),
        borderRadius: BorderRadius.circular(20),
      ),
      child: child,
    );
  }
}

class _ModeBadge extends StatelessWidget {
  final String mode;
  const _ModeBadge(this.mode);

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: AppTheme.primary.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(mode,
        style: const TextStyle(fontSize: 9, fontWeight: FontWeight.w700, color: AppTheme.primary)),
    );
  }
}

class _ModeCard extends StatelessWidget {
  final String id;
  final String label;
  final String desc;
  final IconData icon;
  final bool selected;
  final ValueChanged<String> onTap;

  const _ModeCard({
    required this.id, required this.label, required this.desc,
    required this.icon, required this.selected, required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => onTap(id),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        decoration: BoxDecoration(
          color: selected ? AppTheme.primary.withValues(alpha: 0.15) : AppTheme.surface,
          border: Border.all(
            color: selected ? AppTheme.primary : AppTheme.border,
            width: selected ? 1.5 : 1,
          ),
          borderRadius: BorderRadius.circular(16),
        ),
        child: Row(children: [
          Icon(icon, size: 20, color: selected ? AppTheme.primary : AppTheme.textMuted),
          const SizedBox(width: 8),
          Expanded(child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(label, style: TextStyle(
                fontSize: 12, fontWeight: FontWeight.w700,
                color: selected ? AppTheme.textPrimary : AppTheme.textSecondary,
              )),
              Text(desc, style: const TextStyle(fontSize: 9, color: AppTheme.textMuted)),
            ],
          )),
        ]),
      ),
    );
  }
}

class _StatCard extends StatelessWidget {
  final String label;
  final String value;
  final Color color;
  const _StatCard({required this.label, required this.value, required this.color});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(label, style: const TextStyle(fontSize: 9, color: AppTheme.textMuted,
              fontWeight: FontWeight.w700, letterSpacing: 1)),
            const SizedBox(height: 4),
            Text(value, style: TextStyle(fontSize: 14, fontWeight: FontWeight.w900, color: color)),
          ],
        ),
      ),
    );
  }
}

class _SettingsRow extends StatelessWidget {
  final String icon;
  final String title;
  final String? subtitle;
  final Widget? trailing;

  const _SettingsRow({
    required this.icon, required this.title, this.subtitle, this.trailing,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(children: [
        Text(icon, style: const TextStyle(fontSize: 20)),
        const SizedBox(width: 12),
        Expanded(child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700,
              color: AppTheme.textPrimary)),
            if (subtitle != null)
              Text(subtitle!, style: const TextStyle(fontSize: 11, color: AppTheme.textMuted)),
          ],
        )),
        if (trailing != null) trailing!,
      ]),
    );
  }
}

class _Toggle extends StatelessWidget {
  final bool value;
  final ValueChanged<bool> onChanged;
  const _Toggle({required this.value, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    return Switch(
      value: value,
      onChanged: onChanged,
      activeThumbColor: AppTheme.primary,
    );
  }
}

// ── Payment Bottom Sheet ────────────────────────────────────────────────────
class _PaymentSheet extends StatefulWidget {
  const _PaymentSheet();
  @override
  State<_PaymentSheet> createState() => _PaymentSheetState();
}

class _PaymentSheetState extends State<_PaymentSheet> {
  String _selected = 'quarterly';

  final _plans = [
    {'id': 'monthly',   'label': '1 Месяц',    'price': '5.99',  'badge': null,              'save': null},
    {'id': 'quarterly', 'label': '3 Месяца',   'price': '14.99', 'badge': '🔥 ЛУЧШАЯ ЦЕНА', 'save': '17%'},
    {'id': 'yearly',    'label': '12 Месяцев', 'price': '29.99', 'badge': null,              'save': '37%'},
  ];

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: AppTheme.surface,
        borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
      ),
      padding: EdgeInsets.only(
        left: 20, right: 20, top: 16,
        bottom: MediaQuery.of(context).viewInsets.bottom + 28,
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            // Handle
            Container(
              width: 44, height: 4,
              decoration: BoxDecoration(
                color: AppTheme.border,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
            const SizedBox(height: 20),
            // Header
            Row(
              children: [
                const Text('💎', style: TextStyle(fontSize: 30)),
                const SizedBox(width: 12),
                const Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('SafeNet Premium',
                        style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900,
                          color: AppTheme.textPrimary)),
                      Text('Безлимит · Все серверы · Авто-подключение',
                        style: TextStyle(fontSize: 11, color: AppTheme.textMuted)),
                    ],
                  ),
                ),
                GestureDetector(
                  onTap: () => Navigator.pop(context),
                  child: Container(
                    padding: const EdgeInsets.all(6),
                    decoration: BoxDecoration(
                      color: AppTheme.bg,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Icon(Icons.close, color: AppTheme.textMuted, size: 18),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),
            // Plans
            ..._plans.map((p) => Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: GestureDetector(
                onTap: () => setState(() => _selected = p['id'] as String),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 200),
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                  decoration: BoxDecoration(
                    color: _selected == p['id']
                        ? AppTheme.primary.withValues(alpha: 0.1)
                        : AppTheme.bg,
                    border: Border.all(
                      color: _selected == p['id'] ? AppTheme.primary : AppTheme.border,
                      width: _selected == p['id'] ? 2 : 1,
                    ),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Row(
                    children: [
                      Expanded(child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(children: [
                            Text(p['label'] as String,
                              style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w800,
                                color: AppTheme.textPrimary)),
                            if (p['badge'] != null) ...[
                              const SizedBox(width: 8),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
                                decoration: BoxDecoration(
                                  gradient: const LinearGradient(
                                    colors: [Color(0xFFF59E0B), Color(0xFFF97316)]),
                                  borderRadius: BorderRadius.circular(5),
                                ),
                                child: Text(p['badge'] as String,
                                  style: const TextStyle(fontSize: 8,
                                    fontWeight: FontWeight.w700, color: Colors.white)),
                              ),
                            ],
                          ]),
                          if (p['save'] != null)
                            Text('Экономия ${p['save']}',
                              style: const TextStyle(fontSize: 10, color: AppTheme.success,
                                fontWeight: FontWeight.w700)),
                        ],
                      )),
                      Text('\$${p['price']}',
                        style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w900,
                          color: AppTheme.textPrimary)),
                    ],
                  ),
                ),
              ),
            )),
            const SizedBox(height: 8),
            // Pay button
            Consumer<SubscriptionProvider>(
              builder: (ctx, sub, _) => SizedBox(
                width: double.infinity,
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [Color(0xFF4F46E5), Color(0xFF7C3AED)]),
                    borderRadius: BorderRadius.circular(14),
                    boxShadow: [BoxShadow(
                      color: AppTheme.primary.withValues(alpha: 0.3),
                      blurRadius: 16, offset: const Offset(0, 6))],
                  ),
                  child: ElevatedButton(
                    onPressed: sub.isLoading ? null : () async {
                      final url = await sub.createPurchase(_selected);
                      if (url != null && ctx.mounted) {
                        final uri = Uri.tryParse(url);
                        if (uri != null && await canLaunchUrl(uri)) {
                          await launchUrl(uri, mode: LaunchMode.externalApplication);
                        }
                      }
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.transparent,
                      shadowColor: Colors.transparent,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(14)),
                    ),
                    child: sub.isLoading
                        ? const SizedBox(width: 20, height: 20,
                            child: CircularProgressIndicator(
                              color: Colors.white, strokeWidth: 2))
                        : const Text('Оплатить в CryptoBot',
                            style: TextStyle(fontSize: 15, fontWeight: FontWeight.w900,
                              color: Colors.white)),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 12),
            GestureDetector(
              onTap: () => Navigator.pop(context),
              child: const Text('Продолжить бесплатно →',
                style: TextStyle(fontSize: 12, color: AppTheme.textMuted,
                  fontWeight: FontWeight.w600)),
            ),
          ],
        ),
      ),
    );
  }
}
