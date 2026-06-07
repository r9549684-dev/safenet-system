import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import 'dart:convert';

import '../database/local_db_schema.dart';
import '../domain/models/server_model.dart';

/// Хелпер для работы с локальной базой данных SafeNet (SQLite).
class LocalDbHelper {
  static const _dbName = 'safenet_local.db';
  Database? _db;

  Future<Database> get database async {
    if (_db != null) return _db!;
    _db = await _initDb();
    return _db!;
  }

  Future<Database> _initDb() async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, _dbName);

    return await openDatabase(
      path,
      version: 1,
      onCreate: (db, version) async {
        for (final query in LocalDbSchema.allCreationQueries) {
          await db.execute(query);
        }
      },
    );
  }

  /// Сохранить или обновить сервер в локальной БД.
  Future<void> insertOrUpdateServer(ServerModel server) async {
    final db = await database;
    await db.insert(
      'servers', // Мы должны добавить таблицу servers в схему!
      server.toJson(),
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  /// Получить все серверы (или отфильтрованные по стране).
  Future<List<ServerModel>> getServers({String? countryCode}) async {
    final db = await database;
    final List<Map<String, dynamic>> maps;
    
    if (countryCode != null) {
      maps = await db.query(
        'servers',
        where: 'is_active = 1 AND country = ?',
        whereArgs: [countryCode.toUpperCase()],
        orderBy: 'priority ASC',
      );
    } else {
      maps = await db.query(
        'servers',
        where: 'is_active = 1',
        orderBy: 'priority ASC',
      );
    }

    return maps.map((map) {
      // Декодируем JSON-строку meta обратно в Map, если она есть
      if (map['meta'] is String) {
        try {
          map['meta'] = jsonDecode(map['meta'] as String) as Map<String, dynamic>;
        } catch (_) {
          map['meta'] = null;
        }
      }
      return ServerModel.fromJson(map);
    }).toList();
  }
}
