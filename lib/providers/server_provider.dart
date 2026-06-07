import 'package:flutter/foundation.dart';
import 'dart:convert';
import 'package:dio/dio.dart';

import '../domain/models/server_model.dart';
import '../database/local_db_helper.dart';
import '../data/remote/endpoints.dart';
import '../core/constants.dart';

/// Единая служба управления серверами SafeNet.
/// Отвечает за синхронизацию данных между API и локальной БД,
/// предоставляя реактивный поток активных серверов для UI.
class ServerProvider extends ChangeNotifier {
  final Dio _dio;
  final LocalDbHelper _dbHelper;

  List<ServerModel> _servers = [];
  bool _isLoading = false;
  String? _error;

  ServerProvider({
    Dio? dio,
    LocalDbHelper? dbHelper,
  })  : _dio = dio ??
            Dio(BaseOptions(
              baseUrl: AppConstants.apiBaseUrl,
              connectTimeout: const Duration(seconds: 10),
              receiveTimeout: const Duration(seconds: 15),
            )),
        _dbHelper = dbHelper ?? LocalDbHelper();

  List<ServerModel> get servers => _servers;
  bool get isLoading => _isLoading;
  String? get error => _error;

  /// Загружает серверы из API, сохраняет в локальную БД и обновляет состояние.
  /// Возвращает только активные серверы, отсортированные по приоритету.
  Future<void> fetchAndSyncServers({String? countryCode}) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      // 1. Запрос к API
      final queryParams = <String, dynamic>{};
      if (countryCode != null) queryParams['country'] = countryCode;
      
      final response = await _dio.get(
        Endpoints.servers,
        queryParameters: queryParams.isEmpty ? null : queryParams,
      );

      if (response.statusCode == 200 && response.data is List) {
        final List<dynamic> data = response.data;
        
        // 2. Парсинг и сохранение в локальную БД
        final List<ServerModel> parsedServers = [];
        for (final item in data) {
          if (item is Map<String, dynamic>) {
            final server = ServerModel.fromJson(item);
            if (server.isActive) {
              parsedServers.add(server);
              // Сохраняем/обновляем в локальной БД (включая geo_instructions)
              await _dbHelper.insertOrUpdateServer(server);
            }
          }
        }

        // 3. Сортировка по приоритету (меньшее число = выше приоритет)
        parsedServers.sort((a, b) => a.priority.compareTo(b.priority));
        _servers = parsedServers;
      } else {
        // Fallback: загрузка из локальной БД при ошибке API или неверном формате
        await _loadFromLocalDb(countryCode: countryCode);
      }
    } catch (e) {
      _error = 'Ошибка загрузки серверов: $e';
      debugPrint(_error);
      // При ошибке сети пытаемся загрузить из кэша (локальной БД)
      await _loadFromLocalDb(countryCode: countryCode);
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Загрузка серверов исключительно из локальной базы данных (офлайн-режим / fallback).
  Future<void> _loadFromLocalDb({String? countryCode}) async {
    try {
      final localServers = await _dbHelper.getServers(countryCode: countryCode);
      localServers.sort((a, b) => a.priority.compareTo(b.priority));
      _servers = localServers;
      notifyListeners();
    } catch (e) {
      _error = 'Ошибка чтения из БД: $e';
      debugPrint(_error);
      _servers = [];
      notifyListeners();
    }
  }

  /// Получить конкретный сервер по ID.
  ServerModel? getServerById(String id) {
    try {
      return _servers.firstWhere((s) => s.id == id);
    } catch (e) {
      return null;
    }
  }
}
