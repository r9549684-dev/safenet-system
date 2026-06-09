class Endpoints {
  // Auth
  static const register = '/auth/device';
  static const me       = '/users/me';

  // Servers
  static const servers            = '/servers';
  static const recommendedServer  = '/servers/recommended';
  static String connectServer(String id) => '/service/connect/$id';

  // Subscriptions
  static String pricing([String country = '']) =>
      country.isEmpty ? '/subscriptions/pricing' : '/subscriptions/pricing?country=$country';
  static String purchase(String plan, [String country = '']) =>
      country.isEmpty ? '/subscriptions/purchase/$plan' : '/subscriptions/purchase/$plan?country=$country';
  static const subStatus = '/subscriptions/status';

  // Telegram linking
  static const telegramLinkToken = '/users/telegram-link-token';

  // Promo codes
  static const redeemPromo = '/promocodes/redeem';

  // Referrals
  static const referralStats   = '/referrals/stats';
  static const referralRewards = '/referrals/rewards';
  static const requestPayout   = '/referrals/request-payout';

  // Support AI
  static const supportAsk     = '/support/ask';
  static const supportHistory = '/support/history';

  // Config Cache (горячий запас)
  static String configCached(String token, String country, {int? serverId}) {
    var url = '/config/cached/$token?country=$country';
    if (serverId != null) url += '&server_id=$serverId';
    return url;
  }
  static String configConsume(String token, String country) =>
      '/config/consume/$token?country=$country';
  static const configRotate = '/config/rotate';
}
