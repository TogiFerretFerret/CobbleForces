#include <iostream>
#include <vector>
#include <algorithm>
#include <cassert>

using namespace std;

// =========================================================================
// PROBLEM F: Rewrite The Stars
// RATING: 4000+ (Legendary Grandmaster)
// ALGORITHM: Self-Adjusting Top Tree (Compress-Rake Cluster Decomposition)
// =========================================================================

typedef long long ll;
const ll INF = 1e18;
const int MAXN = 200005; // Updated for N=200,000

// --- DP MATRIX ---
struct Matrix {
    ll mat[2][2];
    
    Matrix() {
        mat[0][0] = mat[0][1] = mat[1][0] = mat[1][1] = -INF;
    }
    
    void init_node(ll w) {
        mat[0][0] = 0;   
        mat[0][1] = -INF;
        mat[1][0] = -INF;
        mat[1][1] = w;   
    }
};

// --- TOP TREE NODE ---
enum NodeType { TypeBase, TypeCompress, TypeRake };

struct Node {
    Node *ch[2]; 
    Node *p;
    NodeType type;
    
    // DP State
    Matrix val;     
    
    // Lazy Tags
    bool rev;       
    
    // Base Node Info
    int id;
    ll weight;
    
    Node() {
        ch[0] = ch[1] = p = nullptr;
        type = TypeBase;
        rev = false;
        id = 0;
        weight = 0;
        val.init_node(0);
    }
};

// Increased pool size to accommodate larger N
Node pool[MAXN]; 
int ptr = 0;

Node* new_node() {
    return &pool[ptr++];
}

// --- MATRIX MERGE OPERATIONS ---

void merge_compress(const Matrix& L, const Matrix& R, Matrix& Res) {
    for(int i=0; i<2; ++i) { 
        for(int j=0; j<2; ++j) { 
            Res.mat[i][j] = -INF;
            if(L.mat[i][0] > -INF && R.mat[1][j] > -INF)
                Res.mat[i][j] = max(Res.mat[i][j], L.mat[i][0] + R.mat[1][j]);
             if(L.mat[i][1] > -INF && R.mat[0][j] > -INF)
                Res.mat[i][j] = max(Res.mat[i][j], L.mat[i][1] + R.mat[0][j]);
             if(L.mat[i][0] > -INF && R.mat[0][j] > -INF)
                Res.mat[i][j] = max(Res.mat[i][j], L.mat[i][0] + R.mat[0][j]);
        }
    }
}

void merge_rake(const Matrix& L, const Matrix& R, Matrix& Res) {
    ll add_0 = max(R.mat[0][0], R.mat[1][1]);
    ll add_1 = R.mat[0][0];
    
    for(int i=0; i<2; ++i) {
        for(int j=0; j<2; ++j) {
            Res.mat[i][j] = -INF;
            if (i==0 && L.mat[0][j] > -INF)
                Res.mat[0][j] = max(Res.mat[0][j], L.mat[0][j] + add_0);
            if (i==1 && L.mat[1][j] > -INF)
                Res.mat[1][j] = max(Res.mat[1][j], L.mat[1][j] + add_1);
        }
    }
}

// --- TREE MAINTENANCE ---

void push_up(Node* t) {
    if (!t) return;
    if (t->type == TypeBase) {
        t->val.init_node(t->weight);
        return;
    }
    if (t->type == TypeCompress) {
        if (t->ch[0] && t->ch[1]) {
            merge_compress(t->ch[0]->val, t->ch[1]->val, t->val);
        } else if (t->ch[0]) {
            t->val = t->ch[0]->val;
        } else if (t->ch[1]) {
            t->val = t->ch[1]->val;
        }
    } 
    else if (t->type == TypeRake) {
        if (t->ch[0] && t->ch[1]) {
            merge_rake(t->ch[0]->val, t->ch[1]->val, t->val);
        } else if (t->ch[0]) {
            t->val = t->ch[0]->val;
        }
    }
}

void push_down(Node* t) {
    if (t && t->rev) {
        if (t->type == TypeCompress) {
            swap(t->ch[0], t->ch[1]);
            Matrix tmp = t->val;
            t->val.mat[0][1] = tmp.mat[1][0];
            t->val.mat[1][0] = tmp.mat[0][1];
            if (t->ch[0]) t->ch[0]->rev ^= 1;
            if (t->ch[1]) t->ch[1]->rev ^= 1;
        }
        t->rev = false;
    }
}

bool is_root(Node* t) {
    return !t->p || (t->p->ch[0] != t && t->p->ch[1] != t);
}

void rotate(Node* t) {
    Node* p = t->p;
    Node* g = p->p;
    int d = (p->ch[1] == t);
    
    if (!is_root(p)) {
        if (g->ch[0] == p) g->ch[0] = t;
        else if (g->ch[1] == p) g->ch[1] = t;
    }
    t->p = g;
    p->ch[d] = t->ch[d^1];
    if (p->ch[d]) p->ch[d]->p = p;
    t->ch[d^1] = p;
    p->p = t;
    push_up(p);
    push_up(t);
}

void splay(Node* t) {
    vector<Node*> stack;
    Node* curr = t;
    while (!is_root(curr)) {
        stack.push_back(curr);
        curr = curr->p;
    }
    stack.push_back(curr);
    while (!stack.empty()) {
        push_down(stack.back());
        stack.pop_back();
    }
    while (!is_root(t)) {
        Node* p = t->p;
        if (!is_root(p)) {
            Node* g = p->p;
            if ((g->ch[1] == p) == (p->ch[1] == t)) rotate(p);
            else rotate(t);
        }
        rotate(t);
    }
}

// --- LINK-CUT OPERATIONS ---

Node* access(Node* u) {
    Node* last = nullptr;
    Node* curr = u;
    while (curr) {
        splay(curr);
        if (curr->ch[1]) curr->ch[1]->type = TypeRake;
        if (last) last->type = TypeCompress;
        
        curr->ch[1] = last;
        push_up(curr);
        last = curr;
        curr = curr->p;
    }
    return last;
}

void make_root(Node* u) {
    access(u);
    splay(u);
    u->rev ^= 1;
    push_down(u);
}

void link(Node* u, Node* v) {
    make_root(u);
    make_root(v);
    u->p = v;
    u->type = TypeRake; 
}

void cut(Node* u, Node* v) {
    make_root(u);
    access(v);
    splay(v);
    if (v->ch[0] == u && !u->ch[1]) {
        v->ch[0] = nullptr;
        u->p = nullptr;
        push_up(v);
    }
}

void update_weight(Node* u, int w) {
    make_root(u);
    u->weight = w;
    push_up(u);
}

ll query_mwis(Node* u) {
    make_root(u);
    return max({u->val.mat[0][0], u->val.mat[0][1], 
                u->val.mat[1][0], u->val.mat[1][1]});
}

// --- MAIN ---
Node* nodes[MAXN]; // Updated array size

int main() {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);
    
    int N, Q;
    if (!(cin >> N >> Q)) return 0;
    
    for(int i=1; i<=N; ++i) {
        nodes[i] = new_node();
        nodes[i]->id = i;
        cin >> nodes[i]->weight;
        push_up(nodes[i]);
    }
    
    int M;
    if (!(cin >> M)) return 0;
    for(int i=0; i<M; ++i) {
        int u, v; cin >> u >> v;
        link(nodes[u], nodes[v]);
    }
    
    for(int i=0; i<Q; ++i) {
        int type; cin >> type;
        if (type == 1) {
            int u, v; cin >> u >> v;
            link(nodes[u], nodes[v]);
        } else if (type == 2) {
            int u, v; cin >> u >> v;
            cut(nodes[u], nodes[v]);
        } else if (type == 3) {
            int u, w; cin >> u >> w;
            update_weight(nodes[u], w);
        } else if (type == 4) {
            int u; cin >> u;
            cout << query_mwis(nodes[u]) << "\n";
        }
    }
    return 0;
}
