import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import 'core/theme.dart';
import 'l10n/app_localizations.dart';
import 'providers/auth_provider.dart';
import 'providers/vpn_provider.dart';
import 'providers/subscription_provider.dart';
import 'providers/affiliate_provider.dart';
import 'screens/splash_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp]);
  SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
    statusBarColor: Colors.transparent,
    statusBarIconBrightness: Brightness.light,
  ));
  runApp(const SafeNetApp());
}

class SafeNetApp extends StatelessWidget {
  const SafeNetApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProvider(create: (_) => VpnProvider()),
        ChangeNotifierProvider(create: (_) => SubscriptionProvider()),
        ChangeNotifierProvider(create: (_) => AffiliateProvider()),
      ],
      child: Consumer<AuthProvider>(
        builder: (_, auth, __) => MaterialApp(
          title: 'SafeNet service',
          debugShowCheckedModeBanner: false,
          theme: AppTheme.forLocale(Locale(auth.language)),
          locale: Locale(auth.language),
          supportedLocales: const [
            Locale('en'), Locale('ru'), Locale('fa'),
            Locale('tr'), Locale('ar'), Locale('ur'), Locale('id'),
          ],
          localizationsDelegates: const [
            AppLocalizations.delegate,
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          home: const SplashScreen(),
        ),
      ),
    );
  }
}

