#include <iostream>
#include <vector>
#include <algorithm>
#include <string>

using namespace std;

const int MAXN = 200005;

// --- SEGMENT TREE (Range Add, Range Sum) ---
struct SegTree {
    long long tree[4 * MAXN];
    long long lazy[4 * MAXN];

    void push(int node, int start, int end) {
        if (lazy[node] != 0) {
            int mid = (start + end) / 2;
            tree[node * 2] += lazy[node] * (mid - start + 1);
            lazy[node * 2] += lazy[node];
            tree[node * 2 + 1] += lazy[node] * (end - mid);
            lazy[node * 2 + 1] += lazy[node];
            lazy[node] = 0;
        }
    }

    void update(int node, int start, int end, int l, int r, int val) {
        if (l > end || r < start) return;
        if (l <= start && end <= r) {
            tree[node] += (long long)val * (end - start + 1);
            lazy[node] += val;
            return;
        }
        push(node, start, end);
        int mid = (start + end) / 2;
        update(node * 2, start, mid, l, r, val);
        update(node * 2 + 1, mid + 1, end, l, r, val);
        tree[node] = tree[node * 2] + tree[node * 2 + 1];
    }

    long long query(int node, int start, int end, int l, int r) {
        if (l > end || r < start) return 0;
        if (l <= start && end <= r) return tree[node];
        push(node, start, end);
        int mid = (start + end) / 2;
        return query(node * 2, start, mid, l, r) + query(node * 2 + 1, mid + 1, end, l, r);
    }
} st;

// --- SUFFIX AUTOMATON ---
struct State {
    int len, link;
    int next[26];
} sam[MAXN * 2];
int sz = 1, last = 0;

void sam_init() {
    sam[0].len = 0;
    sam[0].link = -1;
    for(int i=0; i<26; ++i) sam[0].next[i] = -1;
}

int sam_extend(int c) {
    int cur = sz++;
    sam[cur].len = sam[last].len + 1;
    for(int i=0; i<26; ++i) sam[cur].next[i] = -1;
    int p = last;
    while (p != -1 && sam[p].next[c] == -1) {
        sam[p].next[c] = cur;
        p = sam[p].link;
    }
    if (p == -1) {
        sam[cur].link = 0;
    } else {
        int q = sam[p].next[c];
        if (sam[p].len + 1 == sam[q].len) {
            sam[cur].link = q;
        } else {
            int clone = sz++;
            sam[clone].len = sam[p].len + 1;
            sam[clone].link = sam[q].link;
            for(int i=0; i<26; ++i) sam[clone].next[i] = sam[q].next[i];
            while (p != -1 && sam[p].next[c] == q) {
                sam[p].next[c] = clone;
                p = sam[p].link;
            }
            sam[q].link = sam[cur].link = clone;
        }
    }
    last = cur;
    return cur;
}

// --- LINK-CUT TREE ---
struct Node {
    int ch[2] = {0, 0}, p = 0;
    int last_pos = 0;    
    int tag_pos = 0;     
    int val_len = 0;     
} tr[MAXN * 2];

// Helper to apply tag
void cover(int x, int v) {
    if (!x) return;
    tr[x].last_pos = v;
    tr[x].tag_pos = v;
}

void push_lct(int x) {
    if (tr[x].tag_pos) {
        cover(tr[x].ch[0], tr[x].tag_pos);
        cover(tr[x].ch[1], tr[x].tag_pos);
        tr[x].tag_pos = 0;
    }
}

bool is_root(int x) {
    return tr[tr[x].p].ch[0] != x && tr[tr[x].p].ch[1] != x;
}

void rotate(int x) {
    int y = tr[x].p, z = tr[y].p;
    int k = (tr[y].ch[1] == x);
    if (!is_root(y)) tr[z].ch[tr[z].ch[1] == y] = x;
    tr[x].p = z;
    tr[y].ch[k] = tr[x].ch[k ^ 1];
    if (tr[x].ch[k ^ 1]) tr[tr[x].ch[k ^ 1]].p = y;
    tr[x].ch[k ^ 1] = y;
    tr[y].p = x;
}

int stk[MAXN * 2];
void splay(int x) {
    int y = x, top = 0;
    stk[++top] = y;
    while (!is_root(y)) stk[++top] = y = tr[y].p;
    while (top) push_lct(stk[top--]);

    while (!is_root(x)) {
        int y = tr[x].p, z = tr[y].p;
        if (!is_root(y)) {
            ((tr[y].ch[0] == x) ^ (tr[z].ch[0] == y)) ? rotate(x) : rotate(y);
        }
        rotate(x);
    }
}

void modify_segtree(int u, int old_pos, int new_pos) {
    if (u == 0 || old_pos == 0) return; 
    
    // Find max len in this splay tree (rightmost node)
    int p = u;
    while (tr[p].ch[1]) {
        push_lct(p); // Must push down tags to descend
        p = tr[p].ch[1];
    }
    int max_l = tr[p].val_len;

    // Find min node in this splay tree (leftmost node)
    p = u;
    while (tr[p].ch[0]) {
        push_lct(p); // Must push down tags to descend
        p = tr[p].ch[0];
    }
    int min_node = p;
    // The min length covered by the chain starting at min_node is (len(link(min_node)) + 1)
    int min_l = sam[sam[min_node].link].len + 1;

    st.update(1, 1, MAXN, old_pos - max_l + 1, old_pos - min_l + 1, -1);
}

void access(int x, int new_pos) {
    int t = 0;
    int orig_x = x;
    while (x) {
        splay(x);
        // Note: splay(x) handles push_lct for the path to root of aux tree.
        
        // Before detaching ch[1] (which corresponds to deeper part of heavy chain),
        // we isolate {x, ch[0]} to remove their contribution.
        // However, standard access replaces ch[1] with t.
        // The part of the chain changing color is (x and above).
        // Since x is splayed, x and ch[0] represent the upper part of the chain segment in this splay component.
        // ch[1] is the lower part.
        // We are cutting ch[1] off. It keeps old color.
        
        // We need to remove contribution of {x, ch[0]}.
        // The old color is stored in x (and effectively ch[0] via tags).
        // But to accurately find min/max len of {x, ch[0]}, we should temporarily cut ch[1].
        
        // IMPORTANT: modify_segtree traverses the tree to find min/max.
        // It expects a valid splay tree root.
        
        // 1. Temporarily detach right child to form splay tree of {x, ch[0]}
        int old_right = tr[x].ch[1];
        tr[x].ch[1] = 0; 
        // No update_size needed as we don't maintain subtree sizes, just structure.
        
        if (tr[x].last_pos != 0) {
            modify_segtree(x, tr[x].last_pos, new_pos);
        }
        
        // 2. Attach new right child (t)
        tr[x].ch[1] = t;
        // Don't forget tr[old_right].p is still x, but we are effectively switching.
        // LCT parent pointers are handled by rotate/splay, but manual cut needs care?
        // Actually standard access:
        // tr[x].ch[1] = t; if(t) tr[t].p = x;
        // But we just modify ch[1].
        
        t = x;
        x = tr[x].p;
    }
    
    // Now t is the root of the entire preferred path.
    // Add contribution for the whole path.
    // Find max len (rightmost of t)
    int p = t; while(tr[p].ch[1]) { push_lct(p); p = tr[p].ch[1]; }
    int max_l = tr[p].val_len;
    
    // Find min len (leftmost of t)
    p = t; while(tr[p].ch[0]) { push_lct(p); p = tr[p].ch[0]; }
    int min_node = p;
    int min_l = sam[sam[min_node].link].len + 1;
    
    st.update(1, 1, MAXN, new_pos - max_l + 1, new_pos - min_l + 1, 1);
    
    cover(t, new_pos);
}

// --- MAIN ---
int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    string S;
    int Q;
    if (!(cin >> S >> Q)) return 0;
    int n = S.length();

    sam_init();
    vector<int> node_map(n + 1);
    for (int i = 0; i < n; ++i) {
        node_map[i + 1] = sam_extend(S[i] - 'a');
    }

    // Initialize LCT
    for (int i = 1; i < sz; ++i) {
        tr[i].val_len = sam[i].len;
        tr[i].p = sam[i].link; 
        tr[i].last_pos = 0;
    }

    vector<vector<pair<int, int>>> queries(n + 1);
    for (int i = 0; i < Q; ++i) {
        int l, r;
        cin >> l >> r;
        queries[r].push_back({l, i});
    }

    vector<long long> ans(Q);

    for (int r = 1; r <= n; ++r) {
        int u = node_map[r];
        access(u, r);
        
        for (auto& q : queries[r]) {
            int l = q.first;
            ans[q.second] = st.query(1, 1, MAXN, l, r); 
        }
    }

    for (int i = 0; i < Q; ++i) {
        cout << ans[i] << "\n";
    }

    return 0;
}
