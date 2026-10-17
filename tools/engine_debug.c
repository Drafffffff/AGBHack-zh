#include <mgba/core/core.h>
#include <mgba/internal/arm/arm.h>
#include <mgba/internal/arm/isa-inlines.h>
#include <mgba-util/vfs.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
struct mCore *GBACoreCreate(void);
int main(int argc,char**argv){struct mCore*c=GBACoreCreate();c->init(c);mCoreInitConfig(c,0);color_t pix[256*160];c->setVideoBuffer(c,pix,256);c->loadROM(c,VFileOpen(argv[1],0));c->reset(c);struct ARMCore*a=c->cpu;for(int i=0;i<300;i++)c->runFrame(c);c->setKeys(c,8);for(int i=0;i<4;i++)c->runFrame(c);c->setKeys(c,0);for(int i=0;i<180;i++)c->runFrame(c);c->setKeys(c,1);for(int i=0;i<4;i++)c->runFrame(c);c->setKeys(c,0);for(int i=0;i<180;i++)c->runFrame(c);c->setKeys(c,1);for(int i=0;i<4;i++)c->runFrame(c);c->setKeys(c,0);for(int i=0;i<180;i++)c->runFrame(c);size_t ss=c->stateSize(c);void*state=malloc(ss);c->saveState(c,state);char*names[]={"long sword","potion of healing","scroll of identify","wand of wishing","+2 leather armor","2 daggers","ring of protection",0};for(int q=0;names[q];q++){c->loadState(c,state);for(int i=0;i<=strlen(names[q]);i++)c->busWrite8(c,0x0203ff00+i,names[q][i]);unsigned before[3065];for(int k=0;k<3065;k++)before[k]=c->busRead32(c,0x03004004+k*4);a->gprs[0]=0x0203ff00;a->gprs[14]=0x08000101;_ARMSetMode(a,MODE_THUMB);a->gprs[15]=0x08017270;ThumbWritePC(a);int n;for(n=0;n<3000000;n++){c->step(c);if(a->gprs[15]==0x08000102)break;}unsigned o=a->gprs[0];int changed=0;for(int k=0;k<3065;k++)if(before[k]>=0x08000000&&before[k]<0x0a000000&&before[k]!=c->busRead32(c,0x03004004+k*4))changed++;printf("ROM globals changed %d ",changed);printf("%s -> ptr %08x type %u quan %u steps %d PC %08x\n",names[q],o,c->busRead8(c,o+16),c->busRead32(c,o+24),n,a->gprs[15]);}return 0;}
