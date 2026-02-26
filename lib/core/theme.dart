import 'package:flutter/material.dart';

class AppColors {
  static const primary    = Color(0xFF6C63FF);
  static const secondary  = Color(0xFF00D9A5);
  static const background = Color(0xFF0A0E21);
  static const surface    = Color(0xFF1D1E33);
  static const error      = Color(0xFFFF6B6B);
  static const success    = Color(0xFF00D9A5);
  static const warning    = Color(0xFFFFB347);
  static const textPrimary   = Color(0xFFFFFFFF);
  static const textSecondary = Color(0xFFB0B3C6);
}

class AppTheme {
  /// Шрифт для RTL-локалей (фарси, арабский)
  static const String rtlFont = 'Vazirmatn';

  static ThemeData forLocale(Locale locale) => _buildTheme(
    locale.languageCode == 'fa' || locale.languageCode == 'ar'
        ? rtlFont
        : null,
  );

  static ThemeData get dark => _buildTheme(null);

  static ThemeData _buildTheme(String? fontFamily) => ThemeData(
    useMaterial3: true,
    brightness: Brightness.dark,
    scaffoldBackgroundColor: AppColors.background,
    primaryColor: AppColors.primary,
    colorScheme: const ColorScheme.dark(
      primary:    AppColors.primary,
      secondary:  AppColors.secondary,
      surface:    AppColors.surface,
      error:      AppColors.error,
    ),
    appBarTheme: const AppBarTheme(
      backgroundColor: AppColors.background,
      elevation: 0,
      centerTitle: true,
      titleTextStyle: TextStyle(
        color: AppColors.textPrimary,
        fontSize: 18,
        fontWeight: FontWeight.w600,
      ),
    ),
    cardTheme: CardThemeData(
      color: AppColors.surface,
      elevation: 0,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: AppColors.surface,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide.none,
      ),
      hintStyle: const TextStyle(color: AppColors.textSecondary),
    ),
    fontFamily: fontFamily,
    textTheme: TextTheme(
      headlineLarge:  TextStyle(fontSize: 32, fontWeight: FontWeight.bold,  color: AppColors.textPrimary, fontFamily: fontFamily),
      headlineMedium: TextStyle(fontSize: 24, fontWeight: FontWeight.bold,  color: AppColors.textPrimary, fontFamily: fontFamily),
      titleLarge:     TextStyle(fontSize: 18, fontWeight: FontWeight.w600,  color: AppColors.textPrimary, fontFamily: fontFamily),
      bodyLarge:      TextStyle(fontSize: 16, color: AppColors.textSecondary, fontFamily: fontFamily),
      bodyMedium:     TextStyle(fontSize: 14, color: AppColors.textSecondary, fontFamily: fontFamily),
      labelSmall:     TextStyle(fontSize: 11, color: AppColors.textSecondary, fontFamily: fontFamily),
    ),
  );
}
