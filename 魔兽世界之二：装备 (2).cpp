#include<iostream>
#include<iomanip>
using namespace std;
class soilder {
public:
	char* name = NULL;
	unsigned int bloodInit = 0, total = 0;
	int code;
	soilder* next = NULL, * prev = NULL;
	soilder() {};
	soilder(int n) :code(n) {};
	//soilder(unsigned int n) :bloodInit(n) {}
};
class ICEMAN :public soilder {
public:
	char* weapon = NULL;
	ICEMAN() :soilder(0) {};
};
class DRAGON :public soilder {
public:
	char* weapon = NULL;
	float morale = 0;
	DRAGON() :soilder(1) {};
};
class LION :public soilder {
public:
	int loyalty = 0;
	LION() :soilder(2) {};
};
class ninja :public soilder {
public:
	char* weapon[2];
	ninja() :soilder(3) {};
};
class WOLF :public soilder {
public:
	WOLF() :soilder(4) {};
};
class headquarter {
private:
	char team; // 'r':red, 'b':blue
	char weapon[3][10] = { "sword","bomb","arrow" };
public:
	//default: dragon -> ninja -> iceman -> lion -> wolf, 0, 1, 2, 3, 4
	//RED: iceman -> lion -> wolf -> ninja -> dragon, 2, 3, 4, 1, 0
	//BLUE: lion -> dragon -> ninja -> iceman -> wolf, 3, 0, 1, 2, 4
	ICEMAN iceman; 
	LION lion;
	soilder wolf;
	ninja ninja;
	DRAGON dragon; 
	soilder head;
	string color;
	unsigned int M, total = 0;
	bool isStop = false;
	headquarter(unsigned int blood, const unsigned int* s, const char t);
	bool update();
	void print(int count);
};
headquarter::headquarter(unsigned int blood, const unsigned int* s, const char t) {
	iceman.bloodInit = s[0];
	iceman.name = (char*)"iceman";
	lion.bloodInit = s[1];
	lion.name = (char*)"lion";
	wolf.bloodInit = s[2];
	wolf.name = (char*)"wolf";
	ninja.bloodInit = s[3];
	ninja.name = (char*)"ninja";
	dragon.bloodInit = s[4];
	dragon.name = (char*)"dragon";
	M = blood;
	team = t;
	if (team == 'r') {
		iceman.next = &lion;
		lion.next = &wolf;
		wolf.next = &ninja;
		ninja.next = &dragon;
		dragon.next = &iceman;
		head = dragon;
		color = "red";
	}
	else if (team == 'b') {
		lion.next = &dragon;
		dragon.next = &ninja;
		ninja.next = &iceman;
		iceman.next = &wolf;
		wolf.next = &lion;
		head = wolf;
		color = "blue";
	}
	/*else {
		cout << "error on team type" << endl;
	}*/
}
bool headquarter::update() {
	if (M < iceman.bloodInit && M < lion.bloodInit && M < wolf.bloodInit && M < dragon.bloodInit && M < ninja.bloodInit) {
		isStop = true;
		return false;
	}
	else {
		total++;
		while (1) {
			head = *head.next;
			if (M >= head.bloodInit) {
				M -= head.bloodInit;
				head.total++;
				switch (head.code) {
				case 0: // iceman
					iceman.weapon = weapon[total % 3];
					break;
				case 1: // dragon
					dragon.weapon = weapon[total % 3];
					dragon.morale = (float)M / dragon.bloodInit;
					break;
				case 2: // lion
					lion.loyalty = M;
					break;
				case 3: // ninja
					ninja.weapon[0] = weapon[total % 3];
					ninja.weapon[1] = weapon[(total + 1) % 3];
					break;
				case 4: // wolf
					break;
				default:
					break;
				}
				return true;
			}
		}
	}
}
void headquarter::print(int count) {
	cout << setw(3) << setfill('0') << count << ' ';
	if (!isStop) {
		cout << color << ' ' << head.name << ' ' << total << " born with strength " << head.bloodInit << ',';
		cout << head.total << ' ' << head.name << " in " << color << " headquarter" << endl;
		switch (head.code) {
		case 0: // iceman
			cout << "It has a " << iceman.weapon << endl;
			break;
		case 1: // dragon
			cout << "It has a " << dragon.weapon << ",and it's morale is " << setiosflags(ios::fixed) << setprecision(2) << dragon.morale << endl;
			break;
		case 2: // lion
			cout << "It's loyalty is " << lion.loyalty << endl;
			break;
		case 3: // ninja
			cout << "It has a " << ninja.weapon[0] << " and a " << ninja.weapon[1] << endl;
			break;
		case 4:
			break;
		defalut:
			break;
		}
	}
	else {
		//004 blue headquarter stops making warriors
		cout << color << " headquarter stops making warriors" << endl;
	}
}
int main() {
	//红司令部，City 1，City 2，……，City n，蓝司令部
	unsigned int n, M;
	cin >> n;
	for (unsigned int i = 1; i <= n; i++) {
		unsigned int s_in[5] = { 0 }, s_r[5] = { 0 }; //, s_b[5] = {0}
		cin >> M;
		cin >> s_in[0];
		cin >> s_in[1];
		cin >> s_in[2];
		cin >> s_in[3];
		cin >> s_in[4];
		cout << "Case:" << i << endl;
		s_r[0] = s_in[2];
		s_r[1] = s_in[3];
		s_r[2] = s_in[4];
		s_r[3] = s_in[1];
		s_r[4] = s_in[0];
		//s_b[0] = s_in[3];
		//s_b[1] = s_in[0];
		//s_b[2] = s_in[1];
		//s_b[3] = s_in[2];
		//s_b[4] = s_in[4];
		//cout << s_r[0] << ' ' << s_r[1] << ' ' << s_r[2] << ' ' << s_r[3] << ' ' << s_r[4] << endl;
		headquarter red(M, s_r, 'r');
		headquarter blue(M, s_r, 'b');
		int count = 0;
		while (!red.isStop || !blue.isStop) {
			if (!red.isStop) {
				red.update();
				red.print(count);
			}
			if (!blue.isStop) {
				blue.update();
				blue.print(count);

			}
			count++;
		}
		//cout << "hello world" << endl;
	}

	//cout << "hello world" << endl;
	return 0;
}