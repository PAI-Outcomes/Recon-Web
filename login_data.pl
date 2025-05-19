
##use strict;
##use warnings;

use JSON; #if not already installed, just run "cpan JSON"
use CGI;
use DBI;
require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/MyData/RBSReporting_routines.pl";

my $cgi = CGI->new;

print $cgi->header('application/json;charset=UTF-8');

my $login        = $cgi->param('login');    
my @row;

my $db_office  = 'officedb';
my $tbl        = 'weblogin';


&Get_Login_Data;

#convert  data to JSON
my $op = JSON -> new -> utf8 -> pretty(1);
my $json = $op -> encode({
    login      => $row[0]
});

print $json;;

sub Get_Login_Data {

my %attr = ( PrintWarn=>1, RaiseError=>1, PrintError=>1, AutoCommit=>1, InactiveDestroy=>0, HandleError => \&handle_error_batch );
my $dbx = DBI->connect("DBI:mysql:$RIDBNAME:$DBHOST",$dbuser,$dbpwd, \%attr) || &handle_error_batch;

  my $sql;
  my $sthx;
  my $row_cnt;

  $sql = " 
   SELECT upper(login)
     FROM $db_office.$tbl
    WHERE login = upper('$login')
    LIMIT 1
  "; 

  ##print "SQL:\n$sql\n\n" ;

  $sthx    = $dbx->prepare("$sql");
  $row_cnt = $sthx->execute;


  if ( $row_cnt > 0 ) { 
    @row = $sthx->fetchrow_array();
    
  }
  else {
    $row[0] = '';
  }
  $sthx->finish;
}

