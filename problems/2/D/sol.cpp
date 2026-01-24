#include <iostream>
#include <vector>
#include <algorithm>

using namespace std;

typedef long long ll;
const ll INF = 1e18;

// Struct for Convex Hull Trick Line
// Stores y = mx + c and the number of segments (cnt) associated with this optimal transition
struct LineCnt {
    ll m, c;
    int cnt; 
    ll eval(ll x) { return m * x + c; }
};

// Standard Deque CHT for monotonic queries
// Slopes m = -2j are strictly decreasing as j increases.
// Query points x = i are strictly increasing.
struct CHT_Cnt {
    vector<LineCnt> dq;
    int head = 0;

    // Intersection check for Min Hull with decreasing slopes
    // Returns true if l2 is redundant given l1 and l3
    bool bad(LineCnt l1, LineCnt l2, LineCnt l3) {
        // Intersection x of (1,2) >= Intersection x of (2,3)
        // (c2 - c1) / (m1 - m2) >= (c3 - c2) / (m2 - m3)
        // Be careful with sign and overflow. Using __int128.
        return (__int128)(l2.c - l1.c) * (l2.m - l3.m) >= (__int128)(l3.c - l2.c) * (l1.m - l2.m);
    }

    void add(ll m, ll c, int cnt) {
        LineCnt new_line = {m, c, cnt};
        while (dq.size() >= head + 2 && bad(dq[dq.size()-2], dq.back(), new_line)) {
            dq.pop_back();
        }
        dq.push_back(new_line);
    }

    pair<ll, int> query(ll x) {
        // Remove lines that are no longer optimal
        while (head + 1 < dq.size() && dq[head].eval(x) >= dq[head+1].eval(x)) {
            head++;
        }
        return {dq[head].eval(x), dq[head].cnt};
    }
    
    void clear() { 
        dq.clear(); 
        head = 0; 
    }
};

int n, k;
vector<ll> A;
vector<ll> S;
CHT_Cnt cht_cnt;

// DP with Alien's Trick Penalty (lambda)
// Calculates min cost + lambda * count, and returns {cost, count}
pair<ll, int> solve_dp(ll lambda) {
    cht_cnt.clear();
    
    // Base case: dp[0] = 0, count = 0
    // Transition formula:
    // dp[i] = min_{j<i} (dp[j] + (i-j)^2 + (S[i]-S[j]) + lambda)
    //       = i^2 + S[i] + lambda + min_{j<i} (dp[j] + j^2 - S[j] - 2ij)
    // Line for j: m = -2j, c = dp[j] + j^2 - S[j]
    
    // Add line for j=0
    cht_cnt.add(0, 0, 0); 
    
    pair<ll, int> last_res;
    
    for (int i = 1; i <= n; ++i) {
        // Query min for current i
        auto best = cht_cnt.query(i);
        
        ll current_min_val = best.first;
        int current_cnt = best.second + 1;
        
        // Calculate dp[i]
        ll dp_val = current_min_val + (ll)i*i + S[i] + lambda;
        
        last_res = {dp_val, current_cnt};
        
        // Prepare line for future (j=i)
        ll m = -2LL * i;
        ll c = dp_val + (ll)i*i - S[i];
        cht_cnt.add(m, c, current_cnt);
    }
    return last_res;
}

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);
    
    if (!(cin >> n >> k)) return 0;
    
    A.resize(n + 1);
    S.resize(n + 1, 0);
    for (int i = 1; i <= n; ++i) {
        cin >> A[i];
        S[i] = S[i-1] + A[i];
    }

    // Binary search for lambda (Alien's Trick)
    // Range must cover potential derivatives of the cost function.
    // Cost ~ N^2 roughly. Lambda can be large.
    ll l = -1e16, r = 1e16;
    ll ans = 0;

    // We want the smallest lambda such that we use <= k segments?
    // High lambda (penalty) -> Fewer segments.
    // Low lambda -> More segments.
    // We want exactly k. If not reachable (convex hull edge case), we take the bound.
    
    while(l <= r) {
        ll mid = l + (r - l) / 2;
        auto res = solve_dp(mid);
        
        if (res.second <= k) {
            // We used <= k segments. The penalty is high enough (or too high).
            // This is a candidate answer.
            // Formula: Real Cost = DP_Cost - lambda * k
            ans = res.first - (ll)k * mid;
            
            // To see if we can get closer to K (by using more segments), we need LOWER penalty.
            // Wait, usually if cnt <= k, we try to decrease lambda to get more segments?
            // If cnt < k, penalty is too high. Decrease lambda.
            // If cnt == k, we are good, but we might have a range of lambdas.
            // In min-cost WQS, usually we search for the largest lambda s.t. cnt >= k 
            // OR smallest lambda s.t. cnt <= k.
            // Let's stick to standard logic:
            // Decrease lambda => More segments.
            // Increase lambda => Fewer segments.
            // If res.second <= k, we have few segments. To get MORE, we decrease lambda.
            r = mid - 1; 
        } else {
            // res.second > k. We have too many segments. Penalty is too low.
            // Increase lambda.
            l = mid + 1;
        }
    }
    
    cout << ans << endl;
    return 0;
}
