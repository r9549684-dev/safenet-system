class Endpoints {
  // Auth
  static const register = '/auth/device';
  static const me       = '/users/me';

  // Servers
  static const servers            = '/servers';
  static const recommendedServer  = '/servers/recommended';
  static String connectServer(String id) => '/vpn/connect/$id';

  // Subscriptions
  static const pricing  = '/subscriptions/pricing';
  static String purchase(String plan) => '/subscriptions/purchase/$plan';
  static const subStatus = '/subscriptions/status';

  // Promo codes
  static const redeemPromo = '/promocodes/redeem';

  // Referrals
  static const referralStats   = '/referrals/stats';
  static const referralRewards = '/referrals/rewards';
  static const requestPayout   = '/referrals/request-payout';
}
