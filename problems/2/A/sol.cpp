#include <iostream>
#include <vector>
#include <queue>
#include <algorithm>

using namespace std;

/**
 * Problem A: Touko's Perfection
 * * Algorithm: Slope Trick (Priority Queue)
 * Time Complexity: O(N log N)
 * * Explanation:
 * We want to construct a non-decreasing sequence B to minimize sum(|A_i - B_i|).
 * Let F_i(x) be the min cost for the prefix i ending with value x.
 * F_i(x) = |x - A_i| + min_{y <= x} F_{i-1}(y).
 * * The function F is always convex. We track the change points of the slope 
 * using a Max-Priority Queue.
 * * 1. Adding |x - A_i| adds two slope change points at x=A_i (slope -1 -> 0 -> 1).
 * We push A_i twice to the PQ.
 * 2. The prefix min operation (min_{y <= x}) effectively flattens the slope 
 * for all x > optimal_point. This removes the rightmost slope change point.
 * We pop the top of the PQ.
 * 3. The cost increases by the distance between the old optimum and the new point.
 */

int main() {
    // Fast I/O
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    int n;
    if (!(cin >> n)) return 0;

    // Max Priority Queue to store the slope change points of the left side of the valley
    priority_queue<long long> pq;
    long long ans = 0;

    for (int i = 0; i < n; ++i) {
        long long a;
        cin >> a;

        // Push 'a' twice to represent the function |x - a|
        pq.push(a);
        pq.push(a);

        // Remove the rightmost slope change point to satisfy the non-decreasing constraint
        // (This flattens the right side of the convex function)
        long long max_el = pq.top();
        pq.pop();

        // If the old optimum (max_el) is greater than A_i, we pay the difference
        ans += (max_el - a);
    }

    cout << ans << endl;

    return 0;
}
