import 'package:dio/dio.dart';
import '../../core/constants.dart';
import '../../core/errors.dart';
import '../local/secure_storage.dart';

class ApiClient {
  static final ApiClient _i = ApiClient._();
  factory ApiClient() => _i;

  late final Dio _dio;

  ApiClient._() {
    _dio = Dio(BaseOptions(
      baseUrl: AppConstants.apiBaseUrl,
      connectTimeout: AppConstants.connectTimeout,
      receiveTimeout: AppConstants.receiveTimeout,
      headers: {'Content-Type': 'application/json'},
    ));

    _dio.interceptors.addAll([
      _AuthInterceptor(),
      _ErrorInterceptor(),
    ]);
  }

  Future<T> get<T>(String path, {Map<String, dynamic>? params}) async {
    final r = await _dio.get(path, queryParameters: params);
    final raw = r.data;
    if (T == Map<String, dynamic>) {
      return Map<String, dynamic>.from(raw as Map).cast<String, dynamic>() as T;
    }
    return raw as T;
  }

  Future<T> post<T>(String path, {dynamic data, Map<String, dynamic>? params}) async {
    final r = await _dio.post(path, data: data, queryParameters: params);
    final raw = r.data;
    if (T == Map<String, dynamic>) {
      return Map<String, dynamic>.from(raw as Map).cast<String, dynamic>() as T;
    }
    return raw as T;
  }
}

class _AuthInterceptor extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) async {
    final token = await SecureStorage.getToken();
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }
}

class _ErrorInterceptor extends Interceptor {
  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    if (err.type == DioExceptionType.connectionTimeout ||
        err.type == DioExceptionType.receiveTimeout) {
      handler.reject(DioException(
        requestOptions: err.requestOptions,
        error: AppException.network(),
      ));
      return;
    }
    if (err.response?.statusCode == 401) {
      SecureStorage.deleteToken();
      handler.reject(DioException(
        requestOptions: err.requestOptions,
        error: AppException.auth(),
      ));
      return;
    }
    handler.next(err);
  }
}
