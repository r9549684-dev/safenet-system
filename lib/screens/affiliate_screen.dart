import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:qr_flutter/qr_flutter.dart';
import '../config/theme.dart';
import '../providers/affiliate_provider.dart';

class AffiliateScreen extends StatefulWidget {
  const AffiliateScreen({super.key});

  @override
  State<AffiliateScreen> createState() => _AffiliateScreenState();
}

class _AffiliateScreenState extends State<AffiliateScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<AffiliateProvider>().loadProfile();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<AffiliateProvider>(
      builder: (ctx, p, _) {
        if (p.isLoading) {
          return const Scaffold(
            backgroundColor: AppTheme.bg,
            body: Center(child: CircularProgressIndicator(color: AppTheme.primary)),
          );
        }
        return Scaffold(
          backgroundColor: AppTheme.bg,
          appBar: AppBar(
            backgroundColor: AppTheme.surface,
            title: const Text('Реферальная программа',
                style: TextStyle(color: AppTheme.textPrimary, fontWeight: FontWeight.w800)),
            iconTheme: const IconThemeData(color: AppTheme.textPrimary),
          ),
          body: RefreshIndicator(
            onRefresh: p.loadProfile,
            color: AppTheme.primary,
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                if (p.error != null)
                  _ErrorBanner(error: p.error!),
                _StatsCard(profile: p.profile),
                const SizedBox(height: 12),
                _ReferralCodeCard(code: p.profile?['referral_code'] ?? ''),
                const SizedBox(height: 12),
                if (p.profile?['user_type'] == 'partner') ...[
                  _WalletCard(
                    wallet: p.profile?['ton_wallet'],
                    onSave: (w) async {
                      final ok = await p.updateWallet(w);
                      if (ctx.mounted) {
                        ScaffoldMessenger.of(ctx).showSnackBar(SnackBar(
                          content: Text(ok ? 'Кошелёк сохранён' : (p.error ?? 'Ошибка')),
                          backgroundColor: ok ? AppTheme.success : AppTheme.error,
                        ));
                      }
                    },
                  ),
                  const SizedBox(height: 12),
                  _WithdrawCard(
                    balanceTon: (p.profile?['referral_balance_ton'] ?? 0.0).toDouble(),
                    balanceUsd: (p.profile?['referral_balance_usd'] ?? 0.0).toDouble(),
                    canWithdraw: p.profile?['can_withdraw'] ?? false,
                    minTon: (p.profile?['min_withdrawal_ton'] ?? 0.0).toDouble(),
                    onWithdraw: (amount) async {
                      final ok = await p.requestWithdrawal(amount);
                      if (ctx.mounted) {
                        ScaffoldMessenger.of(ctx).showSnackBar(SnackBar(
                          content: Text(ok ? 'Запрос на вывод создан' : (p.error ?? 'Ошибка')),
                          backgroundColor: ok ? AppTheme.success : AppTheme.error,
                        ));
                      }
                    },
                  ),
                  const SizedBox(height: 12),
                  _WithdrawalHistory(withdrawals: p.withdrawals),
                ] else ...[
                  _DiscountCard(),
                  const SizedBox(height: 12),
                  _PartnerTiersCard(),
                  const SizedBox(height: 12),
                  _QrCard(code: p.profile?['referral_code'] ?? ''),
                  const SizedBox(height: 12),
                  _BecomePartnerCard(
                    onApply: (wallet) async {
                      final ok = await p.applyPartner(wallet);
                      if (ctx.mounted) {
                        ScaffoldMessenger.of(ctx).showSnackBar(SnackBar(
                          content: Text(ok ? 'Статус партнёра активирован!' : (p.error ?? 'Ошибка')),
                          backgroundColor: ok ? AppTheme.success : AppTheme.error,
                        ));
                      }
                    },
                  ),
                ],
              ],
            ),
          ),
        );
      },
    );
  }
}

// ── Error Banner ──────────────────────────────────────────────────────────────

class _ErrorBanner extends StatelessWidget {
  final String error;
  const _ErrorBanner({required this.error});

  @override
  Widget build(BuildContext context) => Container(
    margin: const EdgeInsets.only(bottom: 12),
    padding: const EdgeInsets.all(12),
    decoration: BoxDecoration(
      color: AppTheme.error.withOpacity(0.1),
      border: Border.all(color: AppTheme.error.withOpacity(0.3)),
      borderRadius: BorderRadius.circular(12),
    ),
    child: Text(error, style: const TextStyle(color: AppTheme.error, fontSize: 12)),
  );
}

// ── Stats Card ────────────────────────────────────────────────────────────────

class _StatsCard extends StatelessWidget {
  final Map<String, dynamic>? profile;
  const _StatsCard({this.profile});

  @override
  Widget build(BuildContext context) {
    final count = profile?['paid_referrals_count'] ?? 0;
    final rate = profile?['current_rate'];
    final discount = ((profile?['next_payment_discount'] ?? 0.0) * 100).round();
    final isPartner = profile?['user_type'] == 'partner';

    return _GlassCard(
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          const Text('📊 ', style: TextStyle(fontSize: 16)),
          Text('Статистика', style: Theme.of(context).textTheme.titleMedium?.copyWith(
            color: AppTheme.textPrimary, fontWeight: FontWeight.w800)),
          const Spacer(),
          _TypeBadge(isPartner: isPartner),
        ]),
        const SizedBox(height: 16),
        Row(mainAxisAlignment: MainAxisAlignment.spaceAround, children: [
          _StatItem(label: 'Рефералов', value: '$count'),
          if (rate != null)
            _StatItem(label: 'Ставка', value: '${(rate * 100).round()}%', color: AppTheme.success),
          if (discount > 0)
            _StatItem(label: 'Скидка', value: '$discount%', color: AppTheme.warning),
          if (!isPartner && discount == 0)
            _StatItem(label: 'Подключи друга', value: '-50%', color: AppTheme.primary),
        ]),
      ]),
    );
  }
}

class _TypeBadge extends StatelessWidget {
  final bool isPartner;
  const _TypeBadge({required this.isPartner});

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
    decoration: BoxDecoration(
      color: (isPartner ? AppTheme.success : AppTheme.primary).withOpacity(0.15),
      borderRadius: BorderRadius.circular(8),
      border: Border.all(color: (isPartner ? AppTheme.success : AppTheme.primary).withOpacity(0.3)),
    ),
    child: Text(
      isPartner ? 'ПАРТНЁР' : 'ПОЛЬЗОВАТЕЛЬ',
      style: TextStyle(
        fontSize: 10, fontWeight: FontWeight.w800,
        color: isPartner ? AppTheme.success : AppTheme.primary,
        letterSpacing: 1,
      ),
    ),
  );
}

class _StatItem extends StatelessWidget {
  final String label, value;
  final Color? color;
  const _StatItem({required this.label, required this.value, this.color});

  @override
  Widget build(BuildContext context) => Column(children: [
    Text(value, style: TextStyle(
      fontSize: 24, fontWeight: FontWeight.w900,
      color: color ?? AppTheme.textPrimary)),
    Text(label, style: const TextStyle(fontSize: 11, color: AppTheme.textMuted)),
  ]);
}

// ── Referral Code Card ────────────────────────────────────────────────────────

class _ReferralCodeCard extends StatelessWidget {
  final String code;
  const _ReferralCodeCard({required this.code});

  @override
  Widget build(BuildContext context) => _GlassCard(
    child: Row(children: [
      const Text('🔗 ', style: TextStyle(fontSize: 16)),
      Expanded(
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('Реферальный код',
            style: TextStyle(fontSize: 11, color: AppTheme.textMuted, letterSpacing: 1)),
          const SizedBox(height: 4),
          Text(code.isNotEmpty ? code : '—',
            style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w900, color: AppTheme.textPrimary)),
        ]),
      ),
      if (code.isNotEmpty)
        IconButton(
          icon: const Icon(Icons.copy_rounded, color: AppTheme.primary, size: 20),
          onPressed: () {
            Clipboard.setData(ClipboardData(text: code));
            ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Код скопирован'), duration: Duration(seconds: 2)));
          },
        ),
    ]),
  );
}

// ── Progress Card (для не-партнёров) ─────────────────────────────────────────

class _ProgressCard extends StatelessWidget {
  const _ProgressCard();

  @override
  Widget build(BuildContext context) => _GlassCard(
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      const Text('💰 Как зарабатывать',
        style: TextStyle(fontSize: 14, fontWeight: FontWeight.w800, color: AppTheme.textPrimary)),
      const SizedBox(height: 12),
      _ScaleRow(range: 'Обычный юзер', reward: '50% скидка на следующую оплату за каждого реферала'),
      const Divider(color: AppTheme.border, height: 20),
      _ScaleRow(range: '1–99 рефералов', reward: '\$1 фикс за каждого'),
      _ScaleRow(range: '100–500', reward: '10% от суммы оплаты ежемесячно'),
      _ScaleRow(range: '501–1000', reward: '20% от суммы оплаты ежемесячно'),
      _ScaleRow(range: '1000+', reward: '25% от суммы оплаты ежемесячно'),
    ]),
  );
}

class _ScaleRow extends StatelessWidget {
  final String range, reward;
  const _ScaleRow({required this.range, required this.reward});

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 4),
    child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
      SizedBox(
        width: 90,
        child: Text(range, style: const TextStyle(
          fontSize: 11, fontWeight: FontWeight.w700, color: AppTheme.primary)),
      ),
      Expanded(child: Text(reward,
        style: const TextStyle(fontSize: 11, color: AppTheme.textSecondary))),
    ]),
  );
}

// ── Wallet Card ───────────────────────────────────────────────────────────────

class _WalletCard extends StatefulWidget {
  final String? wallet;
  final Future<void> Function(String) onSave;
  const _WalletCard({this.wallet, required this.onSave});

  @override
  State<_WalletCard> createState() => _WalletCardState();
}

class _WalletCardState extends State<_WalletCard> {
  late TextEditingController _ctrl;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _ctrl = TextEditingController(text: widget.wallet ?? '');
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => _GlassCard(
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      const Text('💼 TON Кошелёк',
        style: TextStyle(fontSize: 14, fontWeight: FontWeight.w800, color: AppTheme.textPrimary)),
      const SizedBox(height: 10),
      TextField(
        controller: _ctrl,
        style: const TextStyle(color: AppTheme.textPrimary, fontSize: 13),
        decoration: InputDecoration(
          hintText: '0:abc... или EQabc...',
          hintStyle: const TextStyle(color: AppTheme.textMuted, fontSize: 12),
          filled: true,
          fillColor: AppTheme.bg,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: AppTheme.border),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: AppTheme.border),
          ),
          contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        ),
      ),
      const SizedBox(height: 10),
      SizedBox(
        width: double.infinity,
        child: ElevatedButton(
          onPressed: _saving ? null : () async {
            setState(() => _saving = true);
            await widget.onSave(_ctrl.text.trim());
            if (mounted) setState(() => _saving = false);
          },
          style: ElevatedButton.styleFrom(
            backgroundColor: AppTheme.primary,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          ),
          child: _saving
              ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
              : const Text('Сохранить', style: TextStyle(fontWeight: FontWeight.w800)),
        ),
      ),
    ]),
  );
}

// ── Withdraw Card ─────────────────────────────────────────────────────────────

class _WithdrawCard extends StatefulWidget {
  final double balanceTon, balanceUsd, minTon;
  final bool canWithdraw;
  final Future<void> Function(double) onWithdraw;
  const _WithdrawCard({
    required this.balanceTon, required this.balanceUsd,
    required this.canWithdraw, required this.minTon,
    required this.onWithdraw,
  });

  @override
  State<_WithdrawCard> createState() => _WithdrawCardState();
}

class _WithdrawCardState extends State<_WithdrawCard> {
  final _ctrl = TextEditingController();
  bool _withdrawing = false;

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => _GlassCard(
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      const Text('💸 Баланс',
        style: TextStyle(fontSize: 14, fontWeight: FontWeight.w800, color: AppTheme.textPrimary)),
      const SizedBox(height: 10),
      Text('${widget.balanceTon.toStringAsFixed(4)} TON ≈ \$${widget.balanceUsd.toStringAsFixed(2)}',
        style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w900, color: AppTheme.textPrimary)),
      Text('Минимум: ${widget.minTon.toStringAsFixed(4)} TON (~\$5)',
        style: const TextStyle(fontSize: 11, color: AppTheme.textMuted)),
      const SizedBox(height: 12),
      if (widget.canWithdraw) ...[
        TextField(
          controller: _ctrl,
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          style: const TextStyle(color: AppTheme.textPrimary, fontSize: 13),
          decoration: InputDecoration(
            labelText: 'Сумма TON',
            labelStyle: const TextStyle(color: AppTheme.textMuted),
            filled: true,
            fillColor: AppTheme.bg,
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(12),
              borderSide: const BorderSide(color: AppTheme.border)),
            enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12),
              borderSide: const BorderSide(color: AppTheme.border)),
            contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          ),
        ),
        const SizedBox(height: 10),
        SizedBox(
          width: double.infinity,
          child: ElevatedButton.icon(
            icon: const Icon(Icons.send_rounded, size: 18),
            label: const Text('Вывести', style: TextStyle(fontWeight: FontWeight.w800)),
            onPressed: _withdrawing ? null : () async {
              final amount = double.tryParse(_ctrl.text);
              if (amount == null || amount <= 0) return;
              setState(() => _withdrawing = true);
              await widget.onWithdraw(amount);
              if (mounted) setState(() => _withdrawing = false);
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.success,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
          ),
        ),
      ] else
        Text('Недостаточно средств для вывода',
          style: TextStyle(color: Colors.grey[600], fontSize: 13)),
    ]),
  );
}

// ── Become Partner Card ───────────────────────────────────────────────────────

class _BecomePartnerCard extends StatefulWidget {
  final Future<void> Function(String) onApply;
  const _BecomePartnerCard({required this.onApply});

  @override
  State<_BecomePartnerCard> createState() => _BecomePartnerCardState();
}

class _BecomePartnerCardState extends State<_BecomePartnerCard> {
  final _ctrl = TextEditingController();
  bool _applying = false;

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(16),
    decoration: BoxDecoration(
      gradient: LinearGradient(
        colors: [AppTheme.primary.withOpacity(0.15), AppTheme.success.withOpacity(0.08)],
      ),
      border: Border.all(color: AppTheme.primary.withOpacity(0.3)),
      borderRadius: BorderRadius.circular(20),
    ),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      const Text('🚀 Стать партнёром',
        style: TextStyle(fontSize: 16, fontWeight: FontWeight.w900, color: AppTheme.textPrimary)),
      const SizedBox(height: 8),
      const Text('Доступно от 11 платящих рефералов. Выплаты на TON-кошелёк.',
        style: TextStyle(fontSize: 12, color: AppTheme.textSecondary)),
      const SizedBox(height: 12),
      TextField(
        controller: _ctrl,
        style: const TextStyle(color: AppTheme.textPrimary, fontSize: 13),
        decoration: InputDecoration(
          labelText: 'TON кошелёк для выплат',
          hintText: '0:abc... или EQabc...',
          labelStyle: const TextStyle(color: AppTheme.textMuted),
          hintStyle: const TextStyle(color: AppTheme.textMuted, fontSize: 12),
          filled: true,
          fillColor: AppTheme.bg,
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: AppTheme.border)),
          enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12),
            borderSide: const BorderSide(color: AppTheme.border)),
          contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        ),
      ),
      const SizedBox(height: 12),
      SizedBox(
        width: double.infinity,
        child: DecoratedBox(
          decoration: BoxDecoration(
            gradient: const LinearGradient(colors: [Color(0xFF4F46E5), Color(0xFF7C3AED)]),
            borderRadius: BorderRadius.circular(12),
          ),
          child: ElevatedButton(
            onPressed: _applying ? null : () async {
              if (_ctrl.text.trim().isEmpty) return;
              setState(() => _applying = true);
              await widget.onApply(_ctrl.text.trim());
              if (mounted) setState(() => _applying = false);
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.transparent,
              shadowColor: Colors.transparent,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              padding: const EdgeInsets.symmetric(vertical: 14),
            ),
            child: _applying
                ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                : const Text('Подать заявку',
                    style: TextStyle(fontSize: 15, fontWeight: FontWeight.w900, color: Colors.white)),
          ),
        ),
      ),
    ]),
  );
}

// ── Withdrawal History ────────────────────────────────────────────────────────

class _WithdrawalHistory extends StatelessWidget {
  final List<Map<String, dynamic>> withdrawals;
  const _WithdrawalHistory({required this.withdrawals});

  @override
  Widget build(BuildContext context) {
    if (withdrawals.isEmpty) return const SizedBox.shrink();
    return _GlassCard(
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Text('📋 История выводов',
          style: TextStyle(fontSize: 14, fontWeight: FontWeight.w800, color: AppTheme.textPrimary)),
        const SizedBox(height: 8),
        ...withdrawals.map((w) => ListTile(
          dense: true,
          contentPadding: EdgeInsets.zero,
          title: Text('${w['amount_ton']} TON',
            style: const TextStyle(color: AppTheme.textPrimary, fontWeight: FontWeight.w700)),
          subtitle: Text(
            w['created_at'].toString().length >= 10
                ? w['created_at'].toString().substring(0, 10) : '',
            style: const TextStyle(color: AppTheme.textMuted, fontSize: 11)),
          trailing: _StatusChip(status: w['status'] ?? 'pending'),
        )),
      ]),
    );
  }
}

class _StatusChip extends StatelessWidget {
  final String status;
  const _StatusChip({required this.status});

  @override
  Widget build(BuildContext context) {
    final color = switch (status) {
      'completed'  => AppTheme.success,
      'processing' => AppTheme.warning,
      'rejected'   => AppTheme.error,
      _            => AppTheme.textMuted,
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.15),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Text(status,
        style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: color)),
    );
  }
}

// ── Glass Card ────────────────────────────────────────────────────────────────

class _GlassCard extends StatelessWidget {
  final Widget child;
  const _GlassCard({required this.child});

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(16),
    decoration: BoxDecoration(
      color: AppTheme.surface,
      border: Border.all(color: AppTheme.border),
      borderRadius: BorderRadius.circular(20),
    ),
    child: child,
  );
}
