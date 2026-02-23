import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/theme.dart';
import '../data/local/secure_storage.dart';
import '../providers/auth_provider.dart';
import 'onboarding_screen.dart';
import 'home_screen.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});
  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  // null = ещё проверяем, true = показать пикер, false = идём дальше
  bool? _showPicker;
  bool _navigating = false;

  @override
  void initState() {
    super.initState();
    _checkLanguage();
  }

  Future<void> _checkLanguage() async {
    final lang = await SecureStorage.getLanguage();
    if (!mounted) return;
    if (lang == null || lang.isEmpty) {
      setState(() => _showPicker = true);
    } else {
      setState(() => _showPicker = false);
      _navigate();
    }
  }

  Future<void> _selectLanguage(String lang) async {
    await context.read<AuthProvider>().setLanguage(lang);
    await SecureStorage.setOnboarded(); // пропускаем онбординг
    if (!mounted) return;
    setState(() => _showPicker = false);
    _navigate();
  }

  Future<void> _navigate() async {
    if (_navigating) return;
    _navigating = true;
    await Future.delayed(const Duration(milliseconds: 600));
    if (!mounted) return;

    final onboarded = await SecureStorage.isOnboarded();
    final auth = context.read<AuthProvider>();

    while (auth.state == AuthState.initial) {
      await Future.delayed(const Duration(milliseconds: 100));
    }

    if (!mounted) return;
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(
        builder: (_) => onboarded
            ? const HomeScreen()
            : const OnboardingScreen(),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      body: _showPicker == true ? _buildPicker() : _buildSplash(),
    );
  }

  Widget _buildSplash() {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 100, height: 100,
            decoration: BoxDecoration(
              color: AppColors.primary.withValues(alpha: 0.15),
              shape: BoxShape.circle,
            ),
            child: const Icon(Icons.shield_rounded, size: 56, color: AppColors.primary),
          ),
          const SizedBox(height: 24),
          const Text('SafeNet VPN',
            style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold, color: Colors.white)),
          const SizedBox(height: 8),
          Text('Secure. Private. Free.',
            style: TextStyle(color: Colors.white.withValues(alpha: 0.5))),
          const SizedBox(height: 48),
          const CircularProgressIndicator(color: AppColors.primary, strokeWidth: 2),
        ],
      ),
    );
  }

  Widget _buildPicker() {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Spacer(),
            Container(
              width: 90, height: 90,
              decoration: BoxDecoration(
                color: AppColors.primary.withValues(alpha: 0.15),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.shield_rounded, size: 50, color: AppColors.primary),
            ),
            const SizedBox(height: 16),
            const Text('SafeNet VPN',
              style: TextStyle(fontSize: 26, fontWeight: FontWeight.bold, color: Colors.white)),
            const SizedBox(height: 40),
            const Text(
              'Выберите язык · زبان را انتخاب کنید · Choose language',
              style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 28),
            _LangButton(flag: '🇷🇺', label: 'Русский',  lang: 'ru', onTap: _selectLanguage),
            const SizedBox(height: 12),
            _LangButton(flag: '🇮🇷', label: 'فارسی',    lang: 'fa', onTap: _selectLanguage),
            const SizedBox(height: 12),
            _LangButton(flag: '🇬🇧', label: 'English',  lang: 'en', onTap: _selectLanguage),
            const Spacer(),
          ],
        ),
      ),
    );
  }
}

class _LangButton extends StatelessWidget {
  final String flag;
  final String label;
  final String lang;
  final void Function(String) onTap;

  const _LangButton({
    required this.flag, required this.label,
    required this.lang, required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      child: GestureDetector(
        onTap: () => onTap(lang),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 16),
          decoration: BoxDecoration(
            color: AppColors.surface,
            border: Border.all(color: AppColors.primary.withValues(alpha: 0.25)),
            borderRadius: BorderRadius.circular(16),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(flag, style: const TextStyle(fontSize: 26)),
              const SizedBox(width: 14),
              Text(label,
                style: const TextStyle(
                  fontSize: 17, fontWeight: FontWeight.w700, color: Colors.white)),
            ],
          ),
        ),
      ),
    );
  }
}
