typedef unsigned short u16;typedef unsigned char u8;typedef unsigned int u32;
extern const u8 zh_font[][8];extern const u32 zh_count;
extern void old6(int,int,int,int,int);
volatile u16 *const st=(volatile u16*)0x070003e0;
void render6(int frame,int chr,int attr,int x,int y){
 unsigned ch=chr&255;
 if(x<0||x>=40||y<0||y>=20)return;
 if(ch>=128&&ch<160){st[0]=0x5aa5;st[1]=ch;st[2]=x;st[3]=y;st[4]=frame;old6(frame,32,15,x,y);return;}
 if(ch>=160&&st[0]==0x5aa5&&st[2]+1==x&&st[3]==y&&st[4]==frame){
  unsigned n=(st[1]-128)*96+ch-160;st[0]=0;old6(frame,32,15,x,y);
  if(n>=zh_count)return;
  volatile u16 *v=(volatile u16*)(frame?0x0600a000:0x06000000);
  unsigned fore=15,back=0;int px=(x-1)*6+2;
  for(int r=0;r<8;r++)for(int c=0;c<8;c+=2){
   unsigned bits=zh_font[n][r];unsigned a=(bits&(128>>c))?fore:back,b=(bits&(128>>(c+1)))?fore:back;
   v[(y*8+r)*120+(px+c)/2]=a|(b<<8);
  }return;
 }
 st[0]=0;old6(frame,ch&127,attr,x,y);
}
// The original wish parser uses ASCII grammar and byte offsets. During this
// synchronous call, switch its global object names/descriptions back to ASCII.
// No heap or persistent save memory is borrowed for the pointer restoration.
extern const u32 wish_pair_count,wish_to_ascii[][2],wish_to_zh[][2];
extern void *oldwish(char *);
static u32 remap(u32 value,const u32 tab[][2]){
 unsigned lo=0,hi=wish_pair_count;
 while(lo<hi){unsigned m=(lo+hi)/2;if(tab[m][0]<value)lo=m+1;else hi=m;}
 return lo<wish_pair_count&&tab[lo][0]==value?tab[lo][1]:value;
}
void *wish_ascii(char *text){
 unsigned char changed[384];for(unsigned i=0;i<384;i++)changed[i]=0;
 volatile u32 *p=(volatile u32*)0x03004004;
 const unsigned count=(0x03006fe8-0x03004004)/4;
 for(unsigned i=0;i<count;i++){u32 old=p[i],v=remap(old,wish_to_ascii);if(v!=old){changed[i/8]|=1<<(i%8);p[i]=v;}}
 void *obj=oldwish(text);
 for(unsigned i=0;i<count;i++)if(changed[i/8]&(1<<(i%8)))p[i]=remap(p[i],wish_to_zh);
 return obj;
}
