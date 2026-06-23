import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:safenet_vpn/core/vless_to_singbox.dart';

void main() {
  final validConfig = <String, dynamic>{
    'protocol': 'vless',
    'address': '38.180.253.219',
    'port': 2053,
    'uuid': 'b2f227a9-c334-4d59-9b7f-7a16200f1e7c',
    'flow': 'xtls-rprx-vision',
    'security': 'reality',
    'reality_opts': <String, dynamic>{
      'public_key': 'x_9Kud4M0DXeoERCsUJZmiV-q-k6KPOUoZe20olvxnA',
      'short_id': 'e95c5ddcfff353d0',
      'server_name': 'www.microsoft.com',
      'fingerprint': 'chrome',
    },
  };

  group('VlessSingboxConverter.isValid', () {
    test('returns true for valid config', () {
      expect(VlessSingboxConverter.isValid(validConfig), isTrue);
    });

    test('returns false when uuid is missing', () {
      final bad = Map<String, dynamic>.from(validConfig)..remove('uuid');
      expect(VlessSingboxConverter.isValid(bad), isFalse);
    });

    test('returns false when uuid is empty', () {
      final bad = Map<String, dynamic>.from(validConfig);
      bad['uuid'] = '';
      expect(VlessSingboxConverter.isValid(bad), isFalse);
    });

    test('returns false when address is missing', () {
      final bad = Map<String, dynamic>.from(validConfig)..remove('address');
      expect(VlessSingboxConverter.isValid(bad), isFalse);
    });

    test('returns false when port is missing', () {
      final bad = Map<String, dynamic>.from(validConfig)..remove('port');
      expect(VlessSingboxConverter.isValid(bad), isFalse);
    });

    test('returns false when reality_opts is missing', () {
      final bad = Map<String, dynamic>.from(validConfig)..remove('reality_opts');
      expect(VlessSingboxConverter.isValid(bad), isFalse);
    });

    test('returns false when reality_opts.public_key is empty', () {
      final bad = Map<String, dynamic>.from(validConfig);
      bad['reality_opts'] = <String, dynamic>{
        'public_key': '',
        'short_id': 'abc',
      };
      expect(VlessSingboxConverter.isValid(bad), isFalse);
    });

    test('returns false for empty config', () {
      expect(VlessSingboxConverter.isValid(<String, dynamic>{}), isFalse);
    });
  });

  group('VlessSingboxConverter.toSingboxJson', () {
    test('produces valid JSON with correct outbound structure', () {
      final jsonStr = VlessSingboxConverter.toSingboxJson(validConfig);
      final parsed = jsonDecode(jsonStr) as Map<String, dynamic>;

      expect(parsed.containsKey('outbounds'), isTrue);
      final outbounds = parsed['outbounds'] as List;
      expect(outbounds.length, 1);

      final ob = outbounds[0] as Map<String, dynamic>;
      expect(ob['type'], 'vless');
      expect(ob['tag'], 'proxy');
      expect(ob['server'], '38.180.253.219');
      expect(ob['server_port'], 2053);
      expect(ob['uuid'], 'b2f227a9-c334-4d59-9b7f-7a16200f1e7c');
      expect(ob['flow'], 'xtls-rprx-vision');
    });

    test('TLS block contains reality + utls', () {
      final jsonStr = VlessSingboxConverter.toSingboxJson(validConfig);
      final parsed = jsonDecode(jsonStr) as Map<String, dynamic>;
      final ob = (parsed['outbounds'] as List)[0] as Map<String, dynamic>;
      final tls = ob['tls'] as Map<String, dynamic>;

      expect(tls['enabled'], isTrue);
      expect(tls['server_name'], 'www.microsoft.com');

      final utls = tls['utls'] as Map<String, dynamic>;
      expect(utls['enabled'], isTrue);
      expect(utls['fingerprint'], 'chrome');

      final reality = tls['reality'] as Map<String, dynamic>;
      expect(reality['enabled'], isTrue);
      expect(reality['public_key'], 'x_9Kud4M0DXeoERCsUJZmiV-q-k6KPOUoZe20olvxnA');
      expect(reality['short_id'], 'e95c5ddcfff353d0');
    });

    test('does NOT include transport (sing-box 1.12+ FATAL on tcp for vision)', () {
      final jsonStr = VlessSingboxConverter.toSingboxJson(validConfig);
      final parsed = jsonDecode(jsonStr) as Map<String, dynamic>;
      final ob = (parsed['outbounds'] as List)[0] as Map<String, dynamic>;
      expect(ob.containsKey('transport'), isFalse);
    });

    test('uses defaults for optional reality_opts fields', () {
      final config = <String, dynamic>{
        'address': '1.2.3.4',
        'port': 443,
        'uuid': 'test-uuid',
        'flow': 'xtls-rprx-vision',
        'reality_opts': <String, dynamic>{
          'public_key': 'pk',
          'short_id': 'sid',
        },
      };
      final jsonStr = VlessSingboxConverter.toSingboxJson(config);
      final parsed = jsonDecode(jsonStr) as Map<String, dynamic>;
      final ob = (parsed['outbounds'] as List)[0] as Map<String, dynamic>;
      final tls = ob['tls'] as Map<String, dynamic>;

      expect(tls['server_name'], 'www.microsoft.com');
      expect((tls['utls'] as Map)['fingerprint'], 'chrome');
    });

    test('port as string is parsed to int', () {
      final config = Map<String, dynamic>.from(validConfig);
      config['port'] = '2053';
      final jsonStr = VlessSingboxConverter.toSingboxJson(config);
      final parsed = jsonDecode(jsonStr) as Map<String, dynamic>;
      final ob = (parsed['outbounds'] as List)[0] as Map<String, dynamic>;
      expect(ob['server_port'], 2053);
    });

    test('throws FormatException when uuid is missing', () {
      final bad = Map<String, dynamic>.from(validConfig)..remove('uuid');
      expect(
        () => VlessSingboxConverter.toSingboxJson(bad),
        throwsA(isA<FormatException>()),
      );
    });

    test('throws FormatException when reality_opts is null', () {
      final bad = Map<String, dynamic>.from(validConfig)..remove('reality_opts');
      expect(
        () => VlessSingboxConverter.toSingboxJson(bad),
        throwsA(isA<FormatException>()),
      );
    });

    // ── Phase 1.5: fragment (DPI fingerprint обход) ─────────────────────────

    test('adds fragment packets=tlshello when backend sends it', () {
      final config = Map<String, dynamic>.from(validConfig);
      config['fragment'] = <String, dynamic>{'packets': 'tlshello'};
      final jsonStr = VlessSingboxConverter.toSingboxJson(config);
      final parsed = jsonDecode(jsonStr) as Map<String, dynamic>;
      final ob = (parsed['outbounds'] as List)[0] as Map<String, dynamic>;
      final tls = ob['tls'] as Map<String, dynamic>;

      expect(tls.containsKey('fragment'), isTrue);
      final frag = tls['fragment'] as Map<String, dynamic>;
      expect(frag['packets'], 'tlshello');
      expect(frag.containsKey('length'), isFalse);
      expect(frag.containsKey('interval'), isFalse);
    });

    test('adds full fragment (packets + length + interval) when backend sends all', () {
      final config = Map<String, dynamic>.from(validConfig);
      config['fragment'] = <String, dynamic>{
        'packets': '1-3',
        'length': '10-30',
        'interval': '10-20',
      };
      final jsonStr = VlessSingboxConverter.toSingboxJson(config);
      final parsed = jsonDecode(jsonStr) as Map<String, dynamic>;
      final ob = (parsed['outbounds'] as List)[0] as Map<String, dynamic>;
      final tls = ob['tls'] as Map<String, dynamic>;
      final frag = tls['fragment'] as Map<String, dynamic>;
      expect(frag['packets'], '1-3');
      expect(frag['length'], '10-30');
      expect(frag['interval'], '10-20');
    });

    test('skips fragment block when field is missing (old configs)', () {
      final jsonStr = VlessSingboxConverter.toSingboxJson(validConfig);
      final parsed = jsonDecode(jsonStr) as Map<String, dynamic>;
      final ob = (parsed['outbounds'] as List)[0] as Map<String, dynamic>;
      final tls = ob['tls'] as Map<String, dynamic>;
      expect(tls.containsKey('fragment'), isFalse);
    });

    test('skips fragment when backend sends empty map', () {
      final config = Map<String, dynamic>.from(validConfig);
      config['fragment'] = <String, dynamic>{};
      final jsonStr = VlessSingboxConverter.toSingboxJson(config);
      final parsed = jsonDecode(jsonStr) as Map<String, dynamic>;
      final ob = (parsed['outbounds'] as List)[0] as Map<String, dynamic>;
      final tls = ob['tls'] as Map<String, dynamic>;
      expect(tls.containsKey('fragment'), isFalse);
    });
  });
}
