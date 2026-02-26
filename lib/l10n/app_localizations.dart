import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';
import 'app_localizations_fa.dart';
import 'app_localizations_ru.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale) : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations)!;
  }

  static const LocalizationsDelegate<AppLocalizations> delegate = _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates = <LocalizationsDelegate<dynamic>>[
    delegate,
    GlobalMaterialLocalizations.delegate,
    GlobalCupertinoLocalizations.delegate,
    GlobalWidgetsLocalizations.delegate,
  ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('en'),
    Locale('fa'),
    Locale('ru')
  ];

  /// No description provided for @appName.
  ///
  /// In en, this message translates to:
  /// **'SafeNet VPN'**
  String get appName;

  /// No description provided for @splashTagline.
  ///
  /// In en, this message translates to:
  /// **'Secure. Private. Free.'**
  String get splashTagline;

  /// No description provided for @chooseLanguage.
  ///
  /// In en, this message translates to:
  /// **'Choose language'**
  String get chooseLanguage;

  /// No description provided for @onb1Title.
  ///
  /// In en, this message translates to:
  /// **'SafeNet VPN'**
  String get onb1Title;

  /// No description provided for @onb1Sub.
  ///
  /// In en, this message translates to:
  /// **'Bypass censorship in UAE, Turkey and other countries — invisibly.'**
  String get onb1Sub;

  /// No description provided for @onb2Title.
  ///
  /// In en, this message translates to:
  /// **'Stealth Technology'**
  String get onb2Title;

  /// No description provided for @onb2Sub.
  ///
  /// In en, this message translates to:
  /// **'ByeDPI and AmneziaWG automatically adapt to your ISP.'**
  String get onb2Sub;

  /// No description provided for @onb3Title.
  ///
  /// In en, this message translates to:
  /// **'3 Days Free'**
  String get onb3Title;

  /// No description provided for @onb3Sub.
  ///
  /// In en, this message translates to:
  /// **'Try premium features right now. No registration needed.'**
  String get onb3Sub;

  /// No description provided for @next.
  ///
  /// In en, this message translates to:
  /// **'Next →'**
  String get next;

  /// No description provided for @start.
  ///
  /// In en, this message translates to:
  /// **'Start'**
  String get start;

  /// No description provided for @statusSecureActive.
  ///
  /// In en, this message translates to:
  /// **'Secure Tunnel Active'**
  String get statusSecureActive;

  /// No description provided for @statusOffline.
  ///
  /// In en, this message translates to:
  /// **'Offline'**
  String get statusOffline;

  /// No description provided for @btnConnect.
  ///
  /// In en, this message translates to:
  /// **'CONNECT'**
  String get btnConnect;

  /// No description provided for @btnDisconnect.
  ///
  /// In en, this message translates to:
  /// **'DISCONNECT'**
  String get btnDisconnect;

  /// No description provided for @btnConnecting.
  ///
  /// In en, this message translates to:
  /// **'CONNECTING'**
  String get btnConnecting;

  /// No description provided for @btnStopping.
  ///
  /// In en, this message translates to:
  /// **'STOPPING'**
  String get btnStopping;

  /// No description provided for @btnRetry.
  ///
  /// In en, this message translates to:
  /// **'RETRY'**
  String get btnRetry;

  /// No description provided for @badgePremium.
  ///
  /// In en, this message translates to:
  /// **'PREMIUM ✓'**
  String get badgePremium;

  /// No description provided for @badgeTrial.
  ///
  /// In en, this message translates to:
  /// **'TRIAL: {days} DAYS'**
  String badgeTrial(int days);

  /// No description provided for @removeLimit.
  ///
  /// In en, this message translates to:
  /// **'💎 Remove limit — Premium'**
  String get removeLimit;

  /// No description provided for @bypassModeLabel.
  ///
  /// In en, this message translates to:
  /// **'BYPASS MODE'**
  String get bypassModeLabel;

  /// No description provided for @modeStealthLabel.
  ///
  /// In en, this message translates to:
  /// **'Auto'**
  String get modeStealthLabel;

  /// No description provided for @modeStealthDesc.
  ///
  /// In en, this message translates to:
  /// **'Smart select'**
  String get modeStealthDesc;

  /// No description provided for @modeByedpiLabel.
  ///
  /// In en, this message translates to:
  /// **'Bypass'**
  String get modeByedpiLabel;

  /// No description provided for @modeByedpiDesc.
  ///
  /// In en, this message translates to:
  /// **'Social media'**
  String get modeByedpiDesc;

  /// No description provided for @modeAmneziaLabel.
  ///
  /// In en, this message translates to:
  /// **'Tunnel'**
  String get modeAmneziaLabel;

  /// No description provided for @modeAmneziaDesc.
  ///
  /// In en, this message translates to:
  /// **'Full protection'**
  String get modeAmneziaDesc;

  /// No description provided for @modeHybridLabel.
  ///
  /// In en, this message translates to:
  /// **'Maximum'**
  String get modeHybridLabel;

  /// No description provided for @modeHybridDesc.
  ///
  /// In en, this message translates to:
  /// **'All-in-one'**
  String get modeHybridDesc;

  /// No description provided for @statsDownload.
  ///
  /// In en, this message translates to:
  /// **'Download'**
  String get statsDownload;

  /// No description provided for @statsUpload.
  ///
  /// In en, this message translates to:
  /// **'Upload'**
  String get statsUpload;

  /// No description provided for @statsPing.
  ///
  /// In en, this message translates to:
  /// **'Ping'**
  String get statsPing;

  /// No description provided for @trialLastDay.
  ///
  /// In en, this message translates to:
  /// **'🔴 Last trial day!'**
  String get trialLastDay;

  /// No description provided for @trialFewDays.
  ///
  /// In en, this message translates to:
  /// **'🟡 {days} trial days left'**
  String trialFewDays(int days);

  /// No description provided for @trialManyDays.
  ///
  /// In en, this message translates to:
  /// **'⏳ Trial: {days} days'**
  String trialManyDays(int days);

  /// No description provided for @trialActiveDesc.
  ///
  /// In en, this message translates to:
  /// **'During trial: unlimited like Premium'**
  String get trialActiveDesc;

  /// No description provided for @trialExpiredDesc.
  ///
  /// In en, this message translates to:
  /// **'After trial: 5-minute sessions'**
  String get trialExpiredDesc;

  /// No description provided for @upgradeToPremium.
  ///
  /// In en, this message translates to:
  /// **'Upgrade to Premium →'**
  String get upgradeToPremium;

  /// No description provided for @premiumTitle.
  ///
  /// In en, this message translates to:
  /// **'SafeNet Premium'**
  String get premiumTitle;

  /// No description provided for @premiumSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Unlimited access to all technologies'**
  String get premiumSubtitle;

  /// No description provided for @colTrial.
  ///
  /// In en, this message translates to:
  /// **'TRIAL'**
  String get colTrial;

  /// No description provided for @colPremium.
  ///
  /// In en, this message translates to:
  /// **'PREMIUM'**
  String get colPremium;

  /// No description provided for @featureSessionLen.
  ///
  /// In en, this message translates to:
  /// **'Session duration'**
  String get featureSessionLen;

  /// No description provided for @featureSessionTrialVal.
  ///
  /// In en, this message translates to:
  /// **'3 days unlimited'**
  String get featureSessionTrialVal;

  /// No description provided for @featureSessionPremiumVal.
  ///
  /// In en, this message translates to:
  /// **'Unlimited ♾'**
  String get featureSessionPremiumVal;

  /// No description provided for @featureAutoConnect.
  ///
  /// In en, this message translates to:
  /// **'Auto-connect'**
  String get featureAutoConnect;

  /// No description provided for @featureKillSwitch.
  ///
  /// In en, this message translates to:
  /// **'Kill Switch'**
  String get featureKillSwitch;

  /// No description provided for @featureBypassModes.
  ///
  /// In en, this message translates to:
  /// **'Bypass modes'**
  String get featureBypassModes;

  /// No description provided for @featureAll4.
  ///
  /// In en, this message translates to:
  /// **'All 4'**
  String get featureAll4;

  /// No description provided for @featureServers.
  ///
  /// In en, this message translates to:
  /// **'Servers'**
  String get featureServers;

  /// No description provided for @featureServersTrialVal.
  ///
  /// In en, this message translates to:
  /// **'Basic'**
  String get featureServersTrialVal;

  /// No description provided for @featureServersPremiumVal.
  ///
  /// In en, this message translates to:
  /// **'All countries'**
  String get featureServersPremiumVal;

  /// No description provided for @featurePrioritySupport.
  ///
  /// In en, this message translates to:
  /// **'Priority support'**
  String get featurePrioritySupport;

  /// No description provided for @trialExpiredMsg.
  ///
  /// In en, this message translates to:
  /// **'Trial expired — 5-minute sessions available.'**
  String get trialExpiredMsg;

  /// No description provided for @trialExpiresIn.
  ///
  /// In en, this message translates to:
  /// **'Trial expires in {days} days. While active — full Premium.'**
  String trialExpiresIn(int days);

  /// No description provided for @choosePlan.
  ///
  /// In en, this message translates to:
  /// **'CHOOSE PLAN'**
  String get choosePlan;

  /// No description provided for @plan1m.
  ///
  /// In en, this message translates to:
  /// **'1 Month'**
  String get plan1m;

  /// No description provided for @plan3m.
  ///
  /// In en, this message translates to:
  /// **'3 Months'**
  String get plan3m;

  /// No description provided for @plan12m.
  ///
  /// In en, this message translates to:
  /// **'12 Months'**
  String get plan12m;

  /// No description provided for @badgeBestPrice.
  ///
  /// In en, this message translates to:
  /// **'🔥 BEST PRICE'**
  String get badgeBestPrice;

  /// No description provided for @savingsLabel.
  ///
  /// In en, this message translates to:
  /// **'Save {percent}'**
  String savingsLabel(String percent);

  /// No description provided for @payWithCryptobot.
  ///
  /// In en, this message translates to:
  /// **'Pay with CryptoBot'**
  String get payWithCryptobot;

  /// No description provided for @safePayment.
  ///
  /// In en, this message translates to:
  /// **'SECURE PAYMENT • INSTANT ACTIVATION'**
  String get safePayment;

  /// No description provided for @paymentDesc.
  ///
  /// In en, this message translates to:
  /// **'Payment in USDT / TON via CryptoBot'**
  String get paymentDesc;

  /// No description provided for @sheetSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Unlimited · All servers · Auto-connect'**
  String get sheetSubtitle;

  /// No description provided for @continueFree.
  ///
  /// In en, this message translates to:
  /// **'Continue for free →'**
  String get continueFree;

  /// No description provided for @settingsTitle.
  ///
  /// In en, this message translates to:
  /// **'Settings'**
  String get settingsTitle;

  /// No description provided for @sectionAccount.
  ///
  /// In en, this message translates to:
  /// **'Account'**
  String get sectionAccount;

  /// No description provided for @deviceIdLabel.
  ///
  /// In en, this message translates to:
  /// **'Device ID'**
  String get deviceIdLabel;

  /// No description provided for @expiryLabel.
  ///
  /// In en, this message translates to:
  /// **'Expires'**
  String get expiryLabel;

  /// No description provided for @sectionVpn.
  ///
  /// In en, this message translates to:
  /// **'VPN Settings'**
  String get sectionVpn;

  /// No description provided for @killSwitchDesc.
  ///
  /// In en, this message translates to:
  /// **'Your IP won\'t leak on disconnect'**
  String get killSwitchDesc;

  /// No description provided for @autoConnectLabel.
  ///
  /// In en, this message translates to:
  /// **'Auto-connect'**
  String get autoConnectLabel;

  /// No description provided for @autoConnectDesc.
  ///
  /// In en, this message translates to:
  /// **'On app launch'**
  String get autoConnectDesc;

  /// No description provided for @resetSettings.
  ///
  /// In en, this message translates to:
  /// **'Reset to initial settings'**
  String get resetSettings;

  /// No description provided for @resetDialogTitle.
  ///
  /// In en, this message translates to:
  /// **'Start fresh?'**
  String get resetDialogTitle;

  /// No description provided for @resetDialogContent.
  ///
  /// In en, this message translates to:
  /// **'Everything will start from scratch.'**
  String get resetDialogContent;

  /// No description provided for @cancel.
  ///
  /// In en, this message translates to:
  /// **'Cancel'**
  String get cancel;

  /// No description provided for @confirm.
  ///
  /// In en, this message translates to:
  /// **'Confirm'**
  String get confirm;

  /// No description provided for @affiliateNavTitle.
  ///
  /// In en, this message translates to:
  /// **'Partner program'**
  String get affiliateNavTitle;

  /// No description provided for @affiliateNavSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Earn on referrals'**
  String get affiliateNavSubtitle;

  /// No description provided for @navHome.
  ///
  /// In en, this message translates to:
  /// **'Home'**
  String get navHome;

  /// No description provided for @navServers.
  ///
  /// In en, this message translates to:
  /// **'Servers'**
  String get navServers;

  /// No description provided for @navPremium.
  ///
  /// In en, this message translates to:
  /// **'Premium'**
  String get navPremium;

  /// No description provided for @navOptions.
  ///
  /// In en, this message translates to:
  /// **'Options'**
  String get navOptions;

  /// No description provided for @affiliateAppBarTitle.
  ///
  /// In en, this message translates to:
  /// **'Referral program'**
  String get affiliateAppBarTitle;

  /// No description provided for @walletSaved.
  ///
  /// In en, this message translates to:
  /// **'Wallet saved'**
  String get walletSaved;

  /// No description provided for @withdrawalCreated.
  ///
  /// In en, this message translates to:
  /// **'Withdrawal request created'**
  String get withdrawalCreated;

  /// No description provided for @partnerActivated.
  ///
  /// In en, this message translates to:
  /// **'Partner status activated!'**
  String get partnerActivated;

  /// No description provided for @error.
  ///
  /// In en, this message translates to:
  /// **'Error'**
  String get error;

  /// No description provided for @statsTitle.
  ///
  /// In en, this message translates to:
  /// **'Statistics'**
  String get statsTitle;

  /// No description provided for @referrals.
  ///
  /// In en, this message translates to:
  /// **'Referrals'**
  String get referrals;

  /// No description provided for @rate.
  ///
  /// In en, this message translates to:
  /// **'Rate'**
  String get rate;

  /// No description provided for @discount.
  ///
  /// In en, this message translates to:
  /// **'Discount'**
  String get discount;

  /// No description provided for @connectFriend.
  ///
  /// In en, this message translates to:
  /// **'Bring a friend'**
  String get connectFriend;

  /// No description provided for @typeBadgePartner.
  ///
  /// In en, this message translates to:
  /// **'PARTNER'**
  String get typeBadgePartner;

  /// No description provided for @typeBadgeUser.
  ///
  /// In en, this message translates to:
  /// **'USER'**
  String get typeBadgeUser;

  /// No description provided for @refCodeTitle.
  ///
  /// In en, this message translates to:
  /// **'Referral code'**
  String get refCodeTitle;

  /// No description provided for @codeCopied.
  ///
  /// In en, this message translates to:
  /// **'Code copied'**
  String get codeCopied;

  /// No description provided for @discountCardTitle.
  ///
  /// In en, this message translates to:
  /// **'VPN at 50% price'**
  String get discountCardTitle;

  /// No description provided for @discountCardHeader.
  ///
  /// In en, this message translates to:
  /// **'👥 Bring a friend'**
  String get discountCardHeader;

  /// No description provided for @discountCardDesc.
  ///
  /// In en, this message translates to:
  /// **'Bring 1 to 10 friends — get 50% discount on next payment for each paying referral.'**
  String get discountCardDesc;

  /// No description provided for @discountCardNote.
  ///
  /// In en, this message translates to:
  /// **'1 — 10 friends = 50% discount each'**
  String get discountCardNote;

  /// No description provided for @discountCardInfo.
  ///
  /// In en, this message translates to:
  /// **'Friend scans QR or enters code at install — discount applies automatically'**
  String get discountCardInfo;

  /// No description provided for @partnerTiersTitle.
  ///
  /// In en, this message translates to:
  /// **'Become a partner'**
  String get partnerTiersTitle;

  /// No description provided for @partnerTiersSubtitle.
  ///
  /// In en, this message translates to:
  /// **'From 11 paying referrals — real income in TON'**
  String get partnerTiersSubtitle;

  /// No description provided for @tierColReferrals.
  ///
  /// In en, this message translates to:
  /// **'Referrals'**
  String get tierColReferrals;

  /// No description provided for @tierColFirstPay.
  ///
  /// In en, this message translates to:
  /// **'First payment'**
  String get tierColFirstPay;

  /// No description provided for @tierColMonthly.
  ///
  /// In en, this message translates to:
  /// **'Monthly'**
  String get tierColMonthly;

  /// No description provided for @tierNoteText.
  ///
  /// In en, this message translates to:
  /// **'\$1.5 — one-time at first referral payment\n% — monthly from each subsequent payment'**
  String get tierNoteText;

  /// No description provided for @qrTitle.
  ///
  /// In en, this message translates to:
  /// **'📲 QR code for friends'**
  String get qrTitle;

  /// No description provided for @qrSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Scanned — downloaded — your code already linked'**
  String get qrSubtitle;

  /// No description provided for @copyLink.
  ///
  /// In en, this message translates to:
  /// **'Copy link'**
  String get copyLink;

  /// No description provided for @linkCopied.
  ///
  /// In en, this message translates to:
  /// **'Link copied'**
  String get linkCopied;

  /// No description provided for @walletTitle.
  ///
  /// In en, this message translates to:
  /// **'💼 TON Wallet'**
  String get walletTitle;

  /// No description provided for @saveBtn.
  ///
  /// In en, this message translates to:
  /// **'Save'**
  String get saveBtn;

  /// No description provided for @balanceTitle.
  ///
  /// In en, this message translates to:
  /// **'💸 Balance'**
  String get balanceTitle;

  /// No description provided for @balanceMin.
  ///
  /// In en, this message translates to:
  /// **'Minimum: {ton} TON (~\$5)'**
  String balanceMin(String ton);

  /// No description provided for @withdrawAmount.
  ///
  /// In en, this message translates to:
  /// **'TON amount'**
  String get withdrawAmount;

  /// No description provided for @withdrawBtn.
  ///
  /// In en, this message translates to:
  /// **'Withdraw'**
  String get withdrawBtn;

  /// No description provided for @insufficientFunds.
  ///
  /// In en, this message translates to:
  /// **'Insufficient funds for withdrawal'**
  String get insufficientFunds;

  /// No description provided for @becomePartnerTitle.
  ///
  /// In en, this message translates to:
  /// **'🚀 Become a partner'**
  String get becomePartnerTitle;

  /// No description provided for @becomePartnerDesc.
  ///
  /// In en, this message translates to:
  /// **'Available from 11 paying referrals. Payouts to TON wallet.'**
  String get becomePartnerDesc;

  /// No description provided for @walletHint.
  ///
  /// In en, this message translates to:
  /// **'0:abc... or EQabc...'**
  String get walletHint;

  /// No description provided for @walletForPayouts.
  ///
  /// In en, this message translates to:
  /// **'TON wallet for payouts'**
  String get walletForPayouts;

  /// No description provided for @applyBtn.
  ///
  /// In en, this message translates to:
  /// **'Apply'**
  String get applyBtn;

  /// No description provided for @withdrawHistoryTitle.
  ///
  /// In en, this message translates to:
  /// **'📋 Withdrawal history'**
  String get withdrawHistoryTitle;

  /// No description provided for @promoCodeHint.
  ///
  /// In en, this message translates to:
  /// **'Promo code'**
  String get promoCodeHint;

  /// No description provided for @promoCodeApply.
  ///
  /// In en, this message translates to:
  /// **'Apply'**
  String get promoCodeApply;

  /// No description provided for @promoCodeSuccess.
  ///
  /// In en, this message translates to:
  /// **'✓ Premium for {months} months activated!'**
  String promoCodeSuccess(int months);

  /// No description provided for @promoCodeLabel.
  ///
  /// In en, this message translates to:
  /// **'Have a promo code?'**
  String get promoCodeLabel;

  /// No description provided for @serversTitle.
  ///
  /// In en, this message translates to:
  /// **'Servers'**
  String get serversTitle;

  /// No description provided for @searchCountry.
  ///
  /// In en, this message translates to:
  /// **'Search country...'**
  String get searchCountry;

  /// No description provided for @autoSelectLabel.
  ///
  /// In en, this message translates to:
  /// **'Auto-select'**
  String get autoSelectLabel;

  /// No description provided for @fastestServer.
  ///
  /// In en, this message translates to:
  /// **'Fastest server'**
  String get fastestServer;

  /// No description provided for @supportNavTitle.
  ///
  /// In en, this message translates to:
  /// **'Support'**
  String get supportNavTitle;

  /// No description provided for @supportNavSubtitle.
  ///
  /// In en, this message translates to:
  /// **'FAQ · AI agent'**
  String get supportNavSubtitle;

  /// No description provided for @supportTitle.
  ///
  /// In en, this message translates to:
  /// **'Support'**
  String get supportTitle;

  /// No description provided for @supportSubtitle.
  ///
  /// In en, this message translates to:
  /// **'FAQ and AI agent coming soon'**
  String get supportSubtitle;

  /// No description provided for @supportTelegramTitle.
  ///
  /// In en, this message translates to:
  /// **'Contact support'**
  String get supportTelegramTitle;

  /// No description provided for @supportTelegramDesc.
  ///
  /// In en, this message translates to:
  /// **'Telegram · Fast replies'**
  String get supportTelegramDesc;

  /// No description provided for @supportFaqTitle.
  ///
  /// In en, this message translates to:
  /// **'FAQ'**
  String get supportFaqTitle;

  /// No description provided for @supportFaqDesc.
  ///
  /// In en, this message translates to:
  /// **'Knowledge base coming soon'**
  String get supportFaqDesc;

  /// No description provided for @supportAiTitle.
  ///
  /// In en, this message translates to:
  /// **'AI Support Agent'**
  String get supportAiTitle;

  /// No description provided for @supportAiDesc.
  ///
  /// In en, this message translates to:
  /// **'Smart assistant coming soon'**
  String get supportAiDesc;

  /// No description provided for @supportComingSoon.
  ///
  /// In en, this message translates to:
  /// **'SOON'**
  String get supportComingSoon;

  /// No description provided for @homeEarnTitle.
  ///
  /// In en, this message translates to:
  /// **'Earn with us'**
  String get homeEarnTitle;

  /// No description provided for @homeEarnSubtitle.
  ///
  /// In en, this message translates to:
  /// **'Invite friends — get discounts & income'**
  String get homeEarnSubtitle;

  /// No description provided for @homeInviteTitle.
  ///
  /// In en, this message translates to:
  /// **'👥 Invite a friend — pay half price'**
  String get homeInviteTitle;

  /// No description provided for @sectionServer.
  ///
  /// In en, this message translates to:
  /// **'VPN Profile'**
  String get sectionServer;

  /// No description provided for @serverCardDesc.
  ///
  /// In en, this message translates to:
  /// **'Tap to change server'**
  String get serverCardDesc;

  /// No description provided for @updateTitle.
  ///
  /// In en, this message translates to:
  /// **'Update available'**
  String get updateTitle;

  /// No description provided for @updateMsg.
  ///
  /// In en, this message translates to:
  /// **'Version {version} is available. Update for new features and improvements.'**
  String updateMsg(String version);

  /// No description provided for @updateBtn.
  ///
  /// In en, this message translates to:
  /// **'Update'**
  String get updateBtn;

  /// No description provided for @updateLater.
  ///
  /// In en, this message translates to:
  /// **'Later'**
  String get updateLater;
}

class _AppLocalizationsDelegate extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) => <String>['en', 'fa', 'ru'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {


  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en': return AppLocalizationsEn();
    case 'fa': return AppLocalizationsFa();
    case 'ru': return AppLocalizationsRu();
  }

  throw FlutterError(
    'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
    'an issue with the localizations generation tool. Please file an issue '
    'on GitHub with a reproducible sample app and the gen-l10n configuration '
    'that was used.'
  );
}
