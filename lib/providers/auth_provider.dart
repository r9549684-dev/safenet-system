import 'package:flutter/material.dart';
import '../data/repositories/auth_repo.dart';
import '../data/local/secure_storage.dart';
import '../domain/models/user.dart';

enum AuthState { initial, loading, authenticated, unauthenticated, error }

class AuthProvider extends ChangeNotifier {
  final _repo = AuthRepository();

  AuthState _state = AuthState.initial;
  User?     _user;
  String    _language = 'en';
  String?   _error;

  AuthState get state    => _state;
  User?     get user     => _user;
  String    get language => _language;
  String?   get error    => _error;
  bool get isAuth        => _state == AuthState.authenticated;

  AuthProvider() { _init(); }

  Future<void> _init() async {
    _language = await SecureStorage.getLanguage() ?? 'en';
    _user = await _repo.tryAutoLogin();
    _state = _user != null ? AuthState.authenticated : AuthState.unauthenticated;
    notifyListeners();
  }

  Future<bool> register({required String country, String? referralCode}) async {
    _state = AuthState.loading;
    _error = null;
    notifyListeners();
    try {
      _user = await _repo.register(
        country: country,
        language: _language,
        referralCode: referralCode,
      );
      await SecureStorage.setOnboarded();
      _state = AuthState.authenticated;
      notifyListeners();
      return true;
    } catch (e) {
      _error = e.toString();
      _state = AuthState.error;
      notifyListeners();
      return false;
    }
  }

  Future<void> setLanguage(String lang) async {
    _language = lang;
    await SecureStorage.saveLanguage(lang);
    notifyListeners();
  }

  Future<void> refreshUser() async {
    final user = await _repo.tryAutoLogin();
    if (user != null) {
      _user = user;
      notifyListeners();
    }
  }

  Future<void> logout() async {
    await _repo.logout();
    _user  = null;
    _state = AuthState.unauthenticated;
    notifyListeners();
  }
}
