import 'package:flutter/material.dart';
import '../config/theme.dart';
import '../l10n/app_localizations.dart';
import 'home_screen.dart';

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});
  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen>
    with SingleTickerProviderStateMixin {
  int _step = 0;
  late AnimationController _anim;
  late Animation<double> _fadeAnim;

  List<Map<String, String>> _steps(BuildContext ctx) {
    final l = AppLocalizations.of(ctx);
    return [
      {'emoji': '🛡️', 'title': l.onb1Title, 'sub': l.onb1Sub},
      {'emoji': '⚡', 'title': l.onb2Title, 'sub': l.onb2Sub},
      {'emoji': '🎁', 'title': l.onb3Title, 'sub': l.onb3Sub},
    ];
  }

  @override
  void initState() {
    super.initState();
    _anim = AnimationController(vsync: this, duration: const Duration(milliseconds: 400));
    _fadeAnim = CurvedAnimation(parent: _anim, curve: Curves.easeOut);
    _anim.forward();
  }

  void _next(BuildContext ctx) {
    if (_step < _steps(ctx).length - 1) {
      _anim.reverse().then((_) {
        setState(() => _step++);
        _anim.forward();
      });
    } else {
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => const HomeScreen()),
      );
    }
  }

  @override
  void dispose() {
    _anim.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final steps = _steps(context);
    final step = steps[_step];
    return Scaffold(
      backgroundColor: AppTheme.bg,
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Spacer(),
              FadeTransition(
                opacity: _fadeAnim,
                child: Column(
                  children: [
                    Text(step['emoji']!, style: const TextStyle(fontSize: 80)),
                    const SizedBox(height: 32),
                    Text(
                      step['title']!,
                      style: const TextStyle(
                        fontSize: 28, fontWeight: FontWeight.w900,
                        color: AppTheme.textPrimary, letterSpacing: -0.5,
                      ),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 16),
                    Text(
                      step['sub']!,
                      style: const TextStyle(
                        fontSize: 16, color: AppTheme.textSecondary, height: 1.6,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
              ),
              const Spacer(),
              // Dots
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(steps.length, (i) => AnimatedContainer(
                  duration: const Duration(milliseconds: 300),
                  margin: const EdgeInsets.symmetric(horizontal: 4),
                  width: i == _step ? 32 : 8,
                  height: 6,
                  decoration: BoxDecoration(
                    color: i == _step ? AppTheme.primary : AppTheme.card,
                    borderRadius: BorderRadius.circular(3),
                  ),
                )),
              ),
              const SizedBox(height: 32),
              SizedBox(
                width: double.infinity,
                  child: ElevatedButton(
                  onPressed: () => _next(context),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppTheme.primaryDark,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 18),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                    ),
                    elevation: 0,
                  ),
                  child: Text(
                    _step < steps.length - 1 ? l.next : l.start,
                    style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700),
                  ),
                ),
              ),
              const SizedBox(height: 32),
            ],
          ),
        ),
      ),
    );
  }
}
