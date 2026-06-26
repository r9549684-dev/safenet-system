// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appName => 'SafeNet VPN';

  @override
  String get splashTagline => 'Secure. Private. Free.';

  @override
  String get chooseLanguage => 'Choose language';

  @override
  String get onb1Title => 'SafeNet VPN';

  @override
  String get onb1Sub =>
      'Bypass censorship in UAE, Turkey and other countries — invisibly.';

  @override
  String get onb2Title => 'Stealth Technology';

  @override
  String get onb2Sub => 'ByeDPI and AmneziaWG automatically adapt to your ISP.';

  @override
  String get onb3Title => '3 Days Free';

  @override
  String get onb3Sub =>
      'Try premium features right now. No registration needed.';

  @override
  String get next => 'Next →';

  @override
  String get start => 'Start';

  @override
  String get statusSecureActive => 'Secure Tunnel Active';

  @override
  String get statusOffline => 'Offline';

  @override
  String get btnConnect => 'CONNECT';

  @override
  String get btnDisconnect => 'DISCONNECT';

  @override
  String get btnConnecting => 'CONNECTING';

  @override
  String get btnStopping => 'STOPPING';

  @override
  String get btnRetry => 'RETRY';

  @override
  String get badgePremium => 'PREMIUM ✓';

  @override
  String badgeTrial(int days) {
    return 'TRIAL: $days DAYS';
  }

  @override
  String get badgeExpired => 'EXPIRED';

  @override
  String get removeLimit => '💎 Remove limit — Premium';

  @override
  String get bypassModeLabel => 'BYPASS MODE';

  @override
  String get modeStealthLabel => 'Auto';

  @override
  String get modeStealthDesc => 'Smart select';

  @override
  String get modeByedpiLabel => 'Bypass';

  @override
  String get modeByedpiDesc => 'Social media';

  @override
  String get modeAmneziaLabel => 'Tunnel';

  @override
  String get modeAmneziaDesc => 'Full protection';

  @override
  String get modeHybridLabel => 'Maximum';

  @override
  String get modeHybridDesc => 'All-in-one';

  @override
  String get statsDownload => 'Download';

  @override
  String get statsUpload => 'Upload';

  @override
  String get statsPing => 'Ping';

  @override
  String get trialLastDay => '🔴 Last trial day!';

  @override
  String get trialExpiredBanner => '🔴 Trial expired!';

  @override
  String trialFewDays(int days) {
    return '🟡 $days trial days left';
  }

  @override
  String trialManyDays(int days) {
    return '⏳ Trial: $days days';
  }

  @override
  String get trialActiveDesc => 'During trial: unlimited like Premium';

  @override
  String get trialExpiredDesc => 'After trial: 5-minute sessions';

  @override
  String get upgradeToPremium => 'Upgrade to Premium →';

  @override
  String get premiumTitle => 'SafeNet Premium';

  @override
  String get premiumSubtitle => 'Unlimited access to all technologies';

  @override
  String get colTrial => 'TRIAL';

  @override
  String get colPremium => 'PREMIUM';

  @override
  String get featureSessionLen => 'Session duration';

  @override
  String get featureSessionTrialVal => '3 days unlimited';

  @override
  String get featureSessionPremiumVal => 'Unlimited ♾';

  @override
  String get featureAutoConnect => 'Auto-connect';

  @override
  String get featureKillSwitch => 'Kill Switch';

  @override
  String get featureBypassModes => 'Bypass modes';

  @override
  String get featureAll4 => 'All 4';

  @override
  String get featureServers => 'Servers';

  @override
  String get featureServersTrialVal => 'Basic';

  @override
  String get featureServersPremiumVal => 'All countries';

  @override
  String get featurePrioritySupport => 'Priority support';

  @override
  String get trialExpiredMsg => 'Trial expired — 5-minute sessions available.';

  @override
  String trialExpiresIn(int days) {
    return 'Trial expires in $days days. While active — full Premium.';
  }

  @override
  String get choosePlan => 'CHOOSE PLAN';

  @override
  String get plan1w => '1 Week';

  @override
  String get plan1m => '1 Month';

  @override
  String get plan3m => '3 Months';

  @override
  String get plan12m => '12 Months';

  @override
  String get badgeBestPrice => '🔥 BEST PRICE';

  @override
  String savingsLabel(String percent) {
    return 'Save $percent';
  }

  @override
  String get payWithCryptobot => 'Pay with CryptoBot';

  @override
  String get safePayment => 'SECURE PAYMENT • INSTANT ACTIVATION';

  @override
  String get paymentDesc => 'Payment in USDT TRC20/TON via CryptoBot';

  @override
  String get sheetSubtitle => 'Unlimited · All servers · Auto-connect';

  @override
  String get continueFree => 'Continue for free →';

  @override
  String get settingsTitle => 'Settings';

  @override
  String get sectionAccount => 'Account';

  @override
  String get deviceIdLabel => 'Device ID';

  @override
  String get expiryLabel => 'Expires';

  @override
  String get sectionVpn => 'VPN Settings';

  @override
  String get killSwitchDesc => 'Your IP won\'t leak on disconnect';

  @override
  String get autoConnectLabel => 'Auto-connect';

  @override
  String get autoConnectDesc => 'On app launch';

  @override
  String get resetSettings => 'Reset to initial settings';

  @override
  String get resetDialogTitle => 'Start fresh?';

  @override
  String get resetDialogContent => 'Everything will start from scratch.';

  @override
  String get cancel => 'Cancel';

  @override
  String get confirm => 'Confirm';

  @override
  String get affiliateNavTitle => 'Partner program';

  @override
  String get affiliateNavSubtitle => 'Earn on referrals';

  @override
  String get navHome => 'Home';

  @override
  String get navServers => 'Servers';

  @override
  String get navPremium => 'Premium';

  @override
  String get navOptions => 'Options';

  @override
  String get affiliateAppBarTitle => 'Referral program';

  @override
  String get walletSaved => 'Wallet saved';

  @override
  String get withdrawalCreated => 'Withdrawal request created';

  @override
  String get partnerActivated => 'Partner status activated!';

  @override
  String get error => 'Error';

  @override
  String get statsTitle => 'Statistics';

  @override
  String get referrals => 'Referrals';

  @override
  String get rate => 'Rate';

  @override
  String get discount => 'Discount';

  @override
  String get connectFriend => 'Bring a friend';

  @override
  String get typeBadgePartner => 'PARTNER';

  @override
  String get typeBadgeUser => 'USER';

  @override
  String get refCodeTitle => 'Referral code';

  @override
  String get codeCopied => 'Code copied';

  @override
  String get discountCardTitle => 'VPN at 50% price';

  @override
  String get discountCardHeader => '👥 Bring a friend';

  @override
  String get discountCardDesc =>
      'Bring 1 to 10 friends — get 50% discount on next payment for each paying referral.';

  @override
  String get discountCardNote => '1 — 10 friends = 50% discount each';

  @override
  String get discountCardInfo =>
      'Friend scans QR or enters code at install — discount applies automatically';

  @override
  String get partnerTiersTitle => 'Become a partner';

  @override
  String get partnerTiersSubtitle =>
      'From 11 paying referrals — real income in TON';

  @override
  String get tierColReferrals => 'Referrals';

  @override
  String get tierColFirstPay => 'First payment';

  @override
  String get tierColMonthly => 'Monthly';

  @override
  String get tierNoteText =>
      '\$1.5 — one-time at first referral payment\n% — monthly from each subsequent payment';

  @override
  String get qrTitle => '📲 QR code for friends';

  @override
  String get qrSubtitle => 'Scanned — downloaded — your code already linked';

  @override
  String get copyLink => 'Copy link';

  @override
  String get linkCopied => 'Link copied';

  @override
  String get walletTitle => '💼 TON Wallet';

  @override
  String get saveBtn => 'Save';

  @override
  String get balanceTitle => '💸 Balance';

  @override
  String balanceMin(String ton) {
    return 'Minimum: $ton TON (~\$5)';
  }

  @override
  String get withdrawAmount => 'TON amount';

  @override
  String get withdrawBtn => 'Withdraw';

  @override
  String get insufficientFunds => 'Insufficient funds for withdrawal';

  @override
  String get becomePartnerTitle => '🚀 Become a partner';

  @override
  String get becomePartnerDesc =>
      'Available from 11 paying referrals. Payouts to TON wallet.';

  @override
  String get walletHint => '0:abc... or EQabc...';

  @override
  String get walletForPayouts => 'TON wallet for payouts';

  @override
  String get applyBtn => 'Apply';

  @override
  String get withdrawHistoryTitle => '📋 Withdrawal history';

  @override
  String get promoCodeHint => 'Promo code';

  @override
  String get promoCodeApply => 'Apply';

  @override
  String promoCodeSuccess(int months) {
    return '✓ Premium for $months months activated!';
  }

  @override
  String get linkTelegramBtn => '🔗 Link Telegram';

  @override
  String get promoCodeLabel => 'Have a promo code?';

  @override
  String get serversTitle => 'Servers';

  @override
  String get searchCountry => 'Search country...';

  @override
  String get autoSelectLabel => 'Auto-select';

  @override
  String get fastestServer => 'Fastest server';

  @override
  String get supportNavTitle => 'Support';

  @override
  String get supportNavSubtitle => 'FAQ · AI agent';

  @override
  String get supportTitle => 'Support';

  @override
  String get supportSubtitle => 'FAQ, AI agent and Telegram support';

  @override
  String get supportTelegramTitle => 'Contact support via Telegram';

  @override
  String get supportTelegramDesc => 'Telegram · Fast replies';

  @override
  String get supportFaqTitle => 'FAQ';

  @override
  String get supportFaqDesc => 'Answers to common questions';

  @override
  String get supportAiTitle => 'AI Support Agent';

  @override
  String get supportAiDesc => 'Smart assistant in Telegram';

  @override
  String get supportComingSoon => 'SOON';

  @override
  String get homeEarnTitle => 'Earn with us';

  @override
  String get homeEarnSubtitle => 'Additional income from your subscribers!';

  @override
  String get homeInviteTitle => '👥 Invite a friend — pay half price';

  @override
  String get sectionServer => 'VPN Profile';

  @override
  String get serverCardDesc => 'Tap to change server';

  @override
  String get updateTitle => 'Update available';

  @override
  String updateMsg(String version) {
    return 'Version $version is available. Update for new features and improvements.';
  }

  @override
  String get updateBtn => 'Update';

  @override
  String get updateLater => 'Later';
}
