require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";

use JSON; #if not already installed, just run "cpan JSON"
use CGI;
use DBI;
use Crypt::KeyDerivation ':all';

my $cgi = CGI->new;

my $NCPDP = $cgi->param('NCPDP');  
my $access = $cgi->param('Access');

#### Hashing Settings #####
$iteration_count = 10000;
$hash_name = 'SHA1';
$byte_size  = 24;

($found, $authkey, $pharmacy_id) = &get_validation_key($NCPDP);

if ( $found ) {
  my $salt = '4IVIEW2SUPWRc9EO.' . $NCPDP;

  my $valkey = pbkdf2($NCPDP, $salt, $iteration_count, $hash_name, $byte_size);
  $valkey = encode_base64($valkey);
  chomp($valkey);

  if ($access eq $valkey) {
    print $cgi->header(-type=>'application/json;charset=UTF-8');

    my $op = JSON -> new -> utf8 -> pretty(1);
    my $json = $op -> encode({
      IsSuccess  => true,
      AuthKey    => $authkey
    });

    print $json;;
  }
  else {
    print $cgi->header(-type=>'application/json;charset=UTF-8');

    my $op = JSON -> new -> utf8 -> pretty(1);
    my $json = $op -> encode({
      IsSuccess    => false,
      ErrorMessage => 'Bad Request'
    });

    print $json;;
  }
}
else {
  print $cgi->header(
     -type=>'application/json;charset=UTF-8'
  );

  my $op = JSON -> new -> utf8 -> pretty(1);
  my $json = $op -> encode({
    IsSuccess    => false,
    ErrorMessage => 'Pharmacy Not Found'
  });

  print $json;;
}

exit;

sub get_validation_key {
  my $NCPDP = shift @_;

  my %attr = ( PrintWarn=>1, RaiseError=>1, PrintError=>1, AutoCommit=>1, InactiveDestroy=>0, HandleError => \&handle_error_batch );
  my $dbx = DBI->connect("DBI:mysql:$RIDBNAME:$DBHOST",$dbuser,$dbpwd, \%attr) || &handle_error_batch;

  my $sql;
  my $sthx;
  my $row_cnt;

  $sql = "
   SELECT Pharmacy_ID
     FROM officedb.pharmacy
    WHERE NCPDP = $NCPDP
  "; 

  $sthx    = $dbx->prepare("$sql");
  $row_cnt = $sthx->execute;

  if ( $row_cnt > 0 ) {
    my ($PH_ID) = $sthx->fetchrow_array();
    $sthx->finish();

    my ($salt) = salt_generator();
    my $iteration_count = 10000;
    my $hash_name = 'SHA1';
    my $byte_size  = 24;

    my $authkey = pbkdf2($PH_ID, $salt, $iteration_count, $hash_name, $byte_size);
    $authkey = encode_base64($authkey);
    chomp($authkey);

    $authkey =~ s/[^a-zA-Z0-9,]//g;

    my $sthi = $dbx->prepare("INSERT INTO officedb.weblogin_auth (auth_key, pharmacy_id) VALUES ('$authkey', $PH_ID)");
    $sthi->execute;
    $sthi->finish(); 

    return (1, $authkey, $PH_ID);
  }
  else {
    return 0;
  }

  $sthx->finish;
}

sub salt_generator {
  my @chars = ("A".."Z", "a".."z", 0..9);
  my $salt;
  $salt .= $chars[rand @chars] for 1..16;
  
  return $salt;
}
