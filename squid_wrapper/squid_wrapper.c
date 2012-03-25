/*
   Simple C suid wrapper to force squid to reread configuration
   file and restart the url_rewriter_program

   Please modify the path to squid binary and recompile!
*/
#include <stdio.h>
#include <unistd.h>
#include <errno.h>
#include <sys/types.h> 
#include <stdlib.h>

#define SQUID_BINARY "/usr/sbin/squid3"

int main(int argc, char **argv, char **envp) {
  char *squidprog[] = { SQUID_BINARY, "-k", "reconfigure", NULL };

  setuid( 0 ); 
/*
  system(SQUID_BINARY" -k reconfigure");
*/
  int ret = execve(squidprog[0], squidprog, envp);

  if (ret == -1 )
      perror("Can't reconfigure squid" );
 

  return 0;
}

