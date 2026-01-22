#include <iostream>
#include <string>

using namespace std;

int main() {
    // Optimize I/O operations
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    int N;
    if (!(cin >> N)) return 0;

    long long bocchi_score = 0;
    long long onk_score = 0;

    for (int i = 0; i < N; ++i) {
        string fandom;
        int score;
        cin >> fandom >> score;

        if (fandom == "Bocchi") {
            bocchi_score += score;
        } else {
            onk_score += score;
        }
    }

    if (bocchi_score > onk_score) {
        cout << "Bocchi" << endl;
    } else if (onk_score > bocchi_score) {
        cout << "OshiNoKo" << endl;
    } else {
        cout << "Tie" << endl;
    }

    return 0;
}
