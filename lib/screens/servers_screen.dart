import 'package:flutter/material.dart';
import '../config/theme.dart';
import '../domain/models/server.dart';

class ServersScreen extends StatefulWidget {
  final String currentId;
  final bool embedded;
  final ValueChanged<VpnServer>? onSelect;

  const ServersScreen({
    super.key,
    required this.currentId,
    this.embedded = false,
    this.onSelect,
  });

  @override
  State<ServersScreen> createState() => _ServersScreenState();
}

class _ServersScreenState extends State<ServersScreen> {
  String _search = '';

  @override
  Widget build(BuildContext context) {
    final filtered = VpnServer.defaults
        .where((s) => s.country.toLowerCase().contains(_search.toLowerCase()))
        .toList();

    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Серверы',
            style: TextStyle(fontSize: 24, fontWeight: FontWeight.w900, color: AppTheme.textPrimary)),
          const SizedBox(height: 20),
          // Search
          TextField(
            onChanged: (v) => setState(() => _search = v),
            style: const TextStyle(color: AppTheme.textPrimary),
            decoration: InputDecoration(
              hintText: 'Поиск страны...',
              hintStyle: const TextStyle(color: AppTheme.textMuted),
              filled: true,
              fillColor: AppTheme.surface,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(16),
                borderSide: BorderSide.none,
              ),
              contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
            ),
          ),
          const SizedBox(height: 16),
          // Auto-select
          GestureDetector(
            onTap: () => widget.embedded ? null : Navigator.pop(context),
            child: Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppTheme.primary.withValues(alpha: 0.1),
                border: Border.all(color: AppTheme.primary.withValues(alpha: 0.2)),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Row(children: [
                Container(
                  width: 44, height: 44,
                  decoration: const BoxDecoration(shape: BoxShape.circle, color: AppTheme.primaryDark),
                  child: const Icon(Icons.bolt_rounded, color: Colors.white),
                ),
                const SizedBox(width: 14),
                const Expanded(child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Авто-выбор', style: TextStyle(fontWeight: FontWeight.w700)),
                    Text('Самый быстрый сервер',
                      style: TextStyle(fontSize: 11, color: AppTheme.textMuted)),
                  ],
                )),
                const Icon(Icons.check, color: AppTheme.primary),
              ]),
            ),
          ),
          const SizedBox(height: 10),
          ...filtered.map((s) => Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: GestureDetector(
              onTap: () {
                if (widget.onSelect != null) {
                  widget.onSelect!(s);
                } else {
                  Navigator.pop(context, s);
                }
              },
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppTheme.surface,
                  border: Border.all(
                    color: widget.currentId == s.id ? AppTheme.primary : AppTheme.border,
                    width: widget.currentId == s.id ? 1.5 : 1,
                  ),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Row(children: [
                  Text(s.flag, style: const TextStyle(fontSize: 28)),
                  const SizedBox(width: 14),
                  Expanded(child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(s.country, style: const TextStyle(fontWeight: FontWeight.w700)),
Text(s.cityLabel, style: const TextStyle(fontSize: 11, color: AppTheme.textMuted))
                    ],
                  )),
                  Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
                    Text('${s.ping} ms',
                      style: TextStyle(
                        fontSize: 12, fontWeight: FontWeight.w700,
                        color: s.ping < 30 ? AppTheme.success : AppTheme.warning,
                      )),
                    const SizedBox(height: 4),
                    Row(children: List.generate(4, (i) => Container(
                      width: 4, height: 12, margin: const EdgeInsets.only(left: 2),
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(2),
                        color: i < ((100 - s.load) / 25).round()
                          ? AppTheme.primary : AppTheme.card,
                      ),
                    ))),
                  ]),
                ]),
              ),
            ),
          )),
          const SizedBox(height: 20),
        ],
      ),
    );
  }
}
