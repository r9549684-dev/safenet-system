import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';
import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import '../providers/auth_provider.dart';

class SupportScreen extends StatelessWidget {
  const SupportScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final deviceId = context.read<AuthProvider>().user?.deviceId ?? '';
    return Scaffold(
      backgroundColor: AppTheme.bg,
      appBar: AppBar(
        backgroundColor: AppTheme.bg,
        elevation: 0,
        surfaceTintColor: Colors.transparent,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_rounded, color: AppTheme.textPrimary),
          onPressed: () => Navigator.pop(context),
        ),
        title: Text(l.supportTitle,
          style: const TextStyle(
            color: AppTheme.textPrimary,
            fontWeight: FontWeight.w800,
            fontSize: 18,
          )),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(20, 8, 20, 40),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(l.supportSubtitle,
              style: const TextStyle(fontSize: 13, color: AppTheme.textMuted)),
            const SizedBox(height: 20),

            // ── UUID-карточка ─────────────────────────────────────────────
            if (deviceId.isNotEmpty) ...[
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppTheme.surface,
                  border: Border.all(color: AppTheme.primary.withValues(alpha: 0.25)),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('ВАШ UUID', style: TextStyle(
                      fontSize: 9, fontWeight: FontWeight.w700,
                      color: AppTheme.textMuted, letterSpacing: 3,
                    )),
                    const SizedBox(height: 8),
                    Row(children: [
                      Expanded(
                        child: Text(deviceId,
                          style: const TextStyle(
                            fontSize: 11, fontWeight: FontWeight.w600,
                            color: AppTheme.textPrimary,
                            fontFamily: 'monospace',
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      GestureDetector(
                        onTap: () {
                          Clipboard.setData(ClipboardData(text: deviceId));
                          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                            content: Text('UUID скопирован'),
                            duration: Duration(seconds: 2),
                          ));
                        },
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                          decoration: BoxDecoration(
                            color: AppTheme.primary.withValues(alpha: 0.12),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: const Row(mainAxisSize: MainAxisSize.min, children: [
                            Icon(Icons.copy_rounded, size: 13, color: AppTheme.primary),
                            SizedBox(width: 4),
                            Text('Копировать', style: TextStyle(
                              fontSize: 11, fontWeight: FontWeight.w700,
                              color: AppTheme.primary,
                            )),
                          ]),
                        ),
                      ),
                    ]),
                    const SizedBox(height: 10),
                    const Text(
                      'Сообщите UUID оператору поддержки — он мгновенно увидит ваш аккаунт',
                      style: TextStyle(fontSize: 10, color: AppTheme.textMuted),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),
            ],

            // ── Написать в поддержку ──────────────────────────────────────
            _label('ПОДДЕРЖКА'),
            const SizedBox(height: 10),
            _SupportCard(
              icon: '✈️',
              title: l.supportTelegramTitle,
              subtitle: l.supportTelegramDesc,
              onTap: () {
                final text = deviceId.isNotEmpty
                    ? Uri.encodeComponent('SafeNet Support\nUUID: $deviceId')
                    : '';
                launchUrl(
                  Uri.parse('https://t.me/safenetvpn${text.isNotEmpty ? "?start=$text" : ""}'),
                  mode: LaunchMode.externalApplication,
                );
              },
            ),
            const SizedBox(height: 24),

            // ── Скоро ────────────────────────────────────────────────────
            _label(l.supportComingSoon),
            const SizedBox(height: 10),
            _SupportCard(
              icon: '❓',
              title: l.supportFaqTitle,
              subtitle: l.supportFaqDesc,
              badge: l.supportComingSoon,
            ),
            const SizedBox(height: 12),
            _SupportCard(
              icon: '🤖',
              title: l.supportAiTitle,
              subtitle: l.supportAiDesc,
              badge: l.supportComingSoon,
            ),
          ],
        ),
      ),
    );
  }

  static Widget _label(String text) => Text(
    text.toUpperCase(),
    style: const TextStyle(
      fontSize: 10, fontWeight: FontWeight.w700,
      color: AppTheme.textMuted, letterSpacing: 3,
    ),
  );
}

class _SupportCard extends StatelessWidget {
  final String icon;
  final String title;
  final String subtitle;
  final String? badge;
  final VoidCallback? onTap;

  const _SupportCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    this.badge,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        decoration: BoxDecoration(
          color: AppTheme.surface,
          border: Border.all(
            color: onTap != null ? AppTheme.primary.withValues(alpha: 0.25) : AppTheme.border,
          ),
          borderRadius: BorderRadius.circular(20),
        ),
        child: ListTile(
          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
          leading: Text(icon, style: const TextStyle(fontSize: 26)),
          title: Text(title,
            style: const TextStyle(
              fontSize: 14, fontWeight: FontWeight.w700,
              color: AppTheme.textPrimary,
            )),
          subtitle: Padding(
            padding: const EdgeInsets.only(top: 2),
            child: Text(subtitle,
              style: const TextStyle(fontSize: 11, color: AppTheme.textMuted)),
          ),
          trailing: badge != null
            ? Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: AppTheme.primary.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(badge!,
                  style: const TextStyle(
                    fontSize: 9, fontWeight: FontWeight.w800,
                    color: AppTheme.primary, letterSpacing: 1,
                  )),
              )
            : const Icon(Icons.arrow_forward_ios_rounded, size: 14, color: AppTheme.textMuted),
        ),
      ),
    );
  }
}
