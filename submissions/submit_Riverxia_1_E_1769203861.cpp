#include <bits/stdc++.h>
using namespace std;
typedef long long ll;
static const uint64_t CHRONO_RANDOM = chrono::steady_clock::now().time_since_epoch().count();
static const uint64_t PIDRNDP = (uint64_t)(getpid())*0xbffbffbffULL;
static mt19937_64 PIDRNG(PIDRNDP);
static const uint64_t PIDRND = PIDRNG();
static const uint64_t FIXED_RANDOM = CHRONO_RANDOM ^ PIDRND;
struct CHASH {
    template <typename T> size_t operator()(const T& x) const {
        return hash<T>{}(x) ^ FIXED_RANDOM;
    }
    template <typename T1, typename T2> size_t operator()(const pair<T1, T2>& x) const {
        return (*this)(x.first) ^ ((*this)(x.second) + 0x9e3779b9 + (x.first << 6) + (x.first >> 2));
    }
};
template<class T, class U> istream& operator>>(istream& i, pair<T, U>& p) { return i >> p.first >> p.second; }
template<class T, class U> ostream& operator<<(ostream& o, const pair<T, U>& p) { return o << p.first << " " << p.second; }
template<class T> istream& operator>>(istream& i, vector<T>& v) { for(auto& x : v) i >> x; return i; }
template<class T> ostream& operator<<(ostream& o, const vector<T>& v) { for(int i=0; i<v.size(); ++i) o << v[i] << (i==v.size()-1?"":" "); return o; }
#define m1(x) template<class T, class... U> void x(T&& a, U&&... b)
#define m2(x) (int[]){(x forward<U>(b),0)...}
template<typename T1,typename T2> using hashmap=unordered_map<T1,T2,CHASH>;
template<typename TM> using matrix=vector<vector<TM>>;
using graph=matrix<int>;
template<typename TM> using tensor=vector<matrix<TM>>;
template<typename TM> using hypermatrix=vector<tensor<TM>>;
template<typename TM, TM Val = TM(), typename... Args> auto make(size_t first, Args... args){
	if constexpr(sizeof...(args) == 0){
		return vector<TM>(first, Val);
	} else {
		return vector<decltype(make<TM, Val>(args...))>(first, make<TM, Val>(args...));
	}
}
#define all(x) (x).begin(),(x).end()
#define forn(i,n) for(int i=0;i<(n);++i)
#define f0rn(v,s,e) for(int v=(s);v>(e);--v)
#define fOrn(v,s,e) for(int v=(s);v<(e);++v)
#define INTERACTIVE false
#if INTERACTIVE
m1(out) { cout << forward<T>(a);  m2(cout << " " <<); cout << endl; }//softmod for interactive
m1(debug) { cerr << forward<T>(a);  m2(cerr << " " <<); cerr << "\n"; }
m1(in) { cin >> forward<T>(a); m2(cin >>); }
#else
m1(out) { cout << forward<T>(a);  m2(cout << " " <<); cout << "\n"; }//softmod for interactive
m1(debug) { cerr << forward<T>(a);  m2(cerr << " " <<); cerr << "\n"; }
m1(in) { cin >> forward<T>(a); m2(cin >>); }
#endif
#define MULTITEST false
#define pb push_back
void solve(){
	const int mod=1e9+7,maxprune=8;
	struct PieceShape {int h,w; vector<string> grid;};
	// Hackless unordered_map
	hashmap<char,PieceShape> shapes = {
		{'I',{1,4,{"####"}}},{'O',{2,2,{"##","##"}}},{'T',{2,3,{".#.","###"}}},
		{'L',{2,3,{"..#","###"}}},{'J',{2,3,{"#..","###"}}},
		{'S',{2,3,{".##","##."}}},{'Z',{2,3,{"##.",".##"}}}
	};
	function<vector<string>(vector<string>,char,int,int)> simulate=[&](vector<string> b,char pType,int col,int W)->vector<string>{
		PieceShape p=shapes[pType]; // p.s. what the HECK is kawaikute gomen??? - it seems surprisingly like villainess (which is worse than bloom with you)
		vector<string> tmpg(b.size()+p.h+5,string(W,'.'));
		forn(r,b.size())tmpg[r]=b[r];
		int fy=-1;
		f0rn(y,b.size()+3,-1){
			bool coll=0;forn(pr,p.h){forn(pc,p.w)if(p.grid[pr][pc]=='#'){
				int br=y+(p.h-1-pr);
				if(br<0){coll=1;break;}
				if(br<b.size()&&b[br][col-1+pc]=='#'){coll=1;break;}
			}if (coll)break;}
			if(coll){fy=y+1;break;}
			if(y==0){fy=0;}
		}
		int mrr=0;
		forn(pr,p.h)forn(pc,p.w)if(p.grid[pr][pc]=='#'){
			int ar=fy+(p.h-1-pr);int ac=col-1+pc;
			while(b.size()<=ar)b.pb(string(W,'.'));
			b[ar][ac]='#';
			mrr=max(mrr,ar);
		}
		vector<string> nb;
		for(const string& row:b){
			bool f=1;for(char c:row)if(c=='.')f=0;
			if(!f)nb.pb(row);
		}
		if(nb.size()>maxprune)return {"INVALID"};
		return nb;
	};
	function<matrix<ll>(const matrix<ll>&,const matrix<ll>&)> multiply=[&](const matrix<ll>& a,const matrix<ll>& b)->matrix<ll>{
		matrix<ll> res=make<ll,0>(a.size(),a.size());
		forn(i,a.size())forn(k,a.size())if(a[i][k])forn(j,a.size())res[i][j]=res[i][j]+a[i][k]*b[k][j]%mod;
		return res;
	};
	function<matrix<ll>(matrix<ll>,ll)> power=[&](matrix<ll> a,ll p)->matrix<ll>{
		matrix<ll> res=make<ll,0>(a.size(),a.size());
		forn(i,a.size())res[i][i]=1;
		while(p>0){
			if(p&1)res=multiply(res,a);
			a=multiply(a,a);
			p>>=1;
		}
		return res;
	};
	struct Edge{int v;char type;int col;};
	int w,n,m;ll l;in(w,n,l,m);
	matrix<Edge> adj(n+1);
	forn(i,m){int u,v,c;char t;in(u,v,t,c);adj[u].pb({v,t,c});}
	// BFS to find reachable states (Node, Board)
	map<pair<int,vector<string>>,int> sti;
	vector<pair<int,vector<string>>> its;
	queue<pair<int,vector<string>>> q;
	vector<string> eb;
	sti[{1,eb}]=0;its.pb({1,eb});q.push({1,eb});
	int stc=0;
	while(!q.empty()){
		auto [u,board]=q.front();q.pop(); // i hate auto but structured bindings are BEAUTIFUL
		for(Edge& e:adj[u]){
			vector<string> nb=simulate(board,e.type,e.col,w);
			if(nb.size()==1&&nb[0]=="INVALID")continue;
			pair<int,vector<string>> ns={e.v,nb};
			if(sti.find(ns)==sti.end())sti[ns]=++stc,its.pb(ns),q.push(ns);
	}}	
	matrix<ll> mat=make<ll,0>(stc+1,stc+1);
	forn(i,stc+1){
		auto [u,board] = its[i];
		for(Edge& e:adj[u]){
			vector<string> nb=simulate(board,e.type,e.col,w);
			if(nb.size()==1&&nb[0]=="INVALID")continue;
			int k=sti[{e.v,nb}];
			mat[i][k]=(mat[i][k]+1)%mod;
	}}
	mat=power(mat,l);
	ll ans=0;
	forn(i,stc+1)if(mat[0][i]>0)if(its[i].second.empty())ans=(ans+mat[0][i])%mod;
	out(ans);
}
int main(){
	if(!INTERACTIVE)cin.tie(0)->sync_with_stdio(0);
	int t=1;
	if (MULTITEST) cin>>t;
	forn(i,t)solve();
}


