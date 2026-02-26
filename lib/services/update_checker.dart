import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:url_launcher/url_launcher.dart';
import '../config/theme.dart';
import '../core/constants.dart';
import '../l10n/app_localizations.dart';

class UpdateChecker {
  /// Проверяет версию на бэкенде. Показывает диалог если доступно обновление.
  /// Silent fail — не мешает работе приложения.
  static Future<void> check(BuildContext context) async {
    try {
      final info = await PackageInfo.fromPlatform();
      final currentCode = int.tryParse(info.buildNumber) ?? 1;

      final dio = Dio(BaseOptions(
        baseUrl: AppConstants.apiBaseUrl,
        connectTimeout: const Duration(seconds: 8),
        receiveTimeout: const Duration(seconds: 8),
      ));

      final response = await dio.get<Map<String, dynamic>>('/app/version');
      final data = response.data!;
      final serverCode  = (data['version_code'] as num).toInt();
      final serverVer   = data['version']      as String;
      final downloadUrl = data['download_url'] as String;
      final forceUpdate = (data['force_update'] as bool?) ?? false;

      if (serverCode > currentCode && context.mounted) {
        _showDialog(context,
          version: serverVer,
          downloadUrl: downloadUrl,
          forceUpdate: forceUpdate,
        );
      }
    } catch (_) {
      // Silent fail
    }
  }

  static void _showDialog(
    BuildContext context, {
    required String version,
    required String downloadUrl,
    required bool forceUpdate,
  }) {
    final l = AppLocalizations.of(context);
    showDialog<void>(
      context: context,
      barrierDismissible: !forceUpdate,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppTheme.surface,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: Row(children: [
          const Text('🚀', style: TextStyle(fontSize: 24)),
          const SizedBox(width: 10),
          Text(l.updateTitle,
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w900,
              color: AppTheme.textPrimary)),
        ]),
        content: Text(
          l.updateMsg(version),
          style: const TextStyle(fontSize: 14, color: AppTheme.textSecondary),
        ),
        actionsPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
        actions: [
          if (!forceUpdate)
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: Text(l.updateLater,
                style: const TextStyle(color: AppTheme.textMuted,
                  fontWeight: FontWeight.w600)),
            ),
          SizedBox(
            width: double.infinity,
            child: DecoratedBox(
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [Color(0xFF4F46E5), Color(0xFF7C3AED)]),
                borderRadius: BorderRadius.circular(12),
              ),
              child: ElevatedButton(
                onPressed: () async {
                  final uri = Uri.tryParse(downloadUrl);
                  if (uri != null && await canLaunchUrl(uri)) {
                    await launchUrl(uri, mode: LaunchMode.externalApplication);
                  }
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.transparent,
                  shadowColor: Colors.transparent,
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12)),
                ),
                child: Text(l.updateBtn,
                  style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w900,
                    color: Colors.white)),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
