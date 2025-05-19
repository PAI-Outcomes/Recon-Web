
##use strict;
##use warnings;

use JSON; #if not already installed, just run "cpan JSON"
use CGI;
use DBI;
require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/MyData/RBSReporting_routines.pl";

my $cgi = CGI->new;

print $cgi->header('text/html;charset=UTF-8');

my $comm_id  = $cgi->param('comm_id');
my $message  = $cgi->param('message');
my $action   = $cgi->param('action');    
my $user     = $cgi->param('user');    
my @row;

$message =~ s/\'/\\'/g;
$message =~ s/\"/\\"/g;

my $db_office    = 'reconrxdb';
my $tbl_comm     = 'communication';
my $tbl_comm_dtl = 'communication_dtl';

my %attr = ( PrintWarn=>1, RaiseError=>1, PrintError=>1, AutoCommit=>1, InactiveDestroy=>0, HandleError => \&handle_error_batch );
my $dbx = DBI->connect("DBI:mysql:$RIDBNAME:$DBHOST",$dbuser,$dbpwd, \%attr) || &handle_error_batch;

if ( $action =~ /Reply/i ) {
  $result = &add_message();
}

if ( $action =~ /View/i ) {
  $result = &set_read();
}

print "$result";
#print "$action";

sub add_message {
  my $sql;
  my $row_cnt;

  $sql = "INSERT INTO reconrxdb.communication_dtl (comm_id, user_id, message, attachment)
          VALUES ($comm_id, $user, '$message', '')"; 

  print "SQL:\n$sql\n\n" ;
  $row_cnt = $dbx->do($sql) or die $DBI::errstr;

  if ( $row_cnt != 1 ) {
    $row_cnt = 0;
  }

  $sql = "UPDATE reconrxdb.communication
             SET user_id = $user,
	         status  = 'N',
		 dte_upd = CURRENT_TIMESTAMP
           WHERE id = $comm_id";

  print "SQL:\n$sql\n\n" ;
  $dbx->do($sql) or die $DBI::errstr;

  return ($row_cnt);
}

sub set_read {
  my $sql;
  my $row_cnt;

  $sql = "UPDATE reconrxdb.communication_dtl
             SET dte_read = CURRENT_TIMESTAMP,
	         status   = 'V'
           WHERE comm_id = $comm_id
	     AND status = 'N'
	     AND user_id != '$user'";

  $dbx->do($sql) or die $DBI::errstr;

  $sql = "UPDATE reconrxdb.communication
             SET status  = 'V',
		 dte_upd = CURRENT_TIMESTAMP
           WHERE id = $comm_id
    	     AND status = 'N'
	     AND user_id != '$user'";

  $row_cnt = $dbx->do($sql) or die $DBI::errstr;

  if ( $row_cnt != 1 ) {
    $row_cnt = 0;
  }

  return ($row_cnt);
}
