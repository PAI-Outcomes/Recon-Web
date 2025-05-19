require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);
use DateTime;

my $start = time();
my ($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";

$ret = &ReadParse(*in);
&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

&readsetCookies;

my $sub_type = $in{'sub_type'};
my $bin      = $in{'bin'};
my $status   = $in{'status'};
my $problem  = $in{'problem'};

if ( $USER ) {
   &MyReconRxHeader;
   &ReconRxHeaderBlock;
} else {
   &ReconRxGotoNewLogin;

   print qq#</BODY>\n#;
   print qq#</HTML>\n#;
   exit(0);
}

#______________________________________________________________________________

$dbin     = "R8DBNAME";
$DBNAME   = $DBNAMES{"$dbin"};
$TABLE    = $DBTABN{"$dbin"};
$FIELDS   = $DBFLDS{"$dbin"};
$FIELDS2  = $DBFLDS{"$dbin"} . "2";
$fieldcnt = $#${FIELDS2} + 2;

$dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
       { PrintError => 1, RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";
DBI->trace(1) if ($dbitrace);

if ( $sub_type ) {
  &update_table($sub_type);
}

&displayWebPage;

$dbx->disconnect;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayWebPage {
  print qq#<!-- displayWebPage -->\n#;


  print <<BM;
  <style>
    td { border-top: none; }
  </style>

  <script>
    function edit_record(tpp_name, bin, status, msg) {
      var bin_val = bin + ' - ' + tpp_name;
      document.getElementById("bin").value = bin_val;
      document.getElementById("status").value = status;
      document.getElementById("problem").value = msg;
      document.getElementById("sub_type").value = 'Update';
    }

    function remove_record(bin) {
      if ( confirm("Are you sure you want to remove this record?") == true ) {
        document.getElementById("bin").value = bin;
        document.getElementById("status").value = '';
        document.getElementById("problem").value = '';
        document.getElementById("sub_type").value = 'Delete';
        document.getElementById("stopForm").submit();
      }
    }

    function clearSearch(frm) {
      tags = frm.getElementsByTagName('input');
      for(i = 0; i < tags.length; i++) {
        if ( tags[i].type == 'text' ) {
          tags[i].value = '';
        }
      }
      tags = frm.getElementsByTagName('select');
      for(i = 0; i < tags.length; i++) {
        tags[i].selectedIndex = 0;
      }
      document.getElementById("sub_type").value = 'Save';
    }
  </script>
BM

  print qq#<form id="stopForm" action="$PROG" method="post" style="display: inline-block; padding-right: 30px;">#;
  print qq#<td><input type="hidden" name="sub_type" id="sub_type" value="Add">\n#;
  print "<table>\n";

  print qq#<tr><td><label for="BinNumber">Third Party Payer:</label></td>#;
  print qq#<td><input type="text" name="bin" list="blist" id="bin" value="" style="width:300px;">\n#;
  print qq#<datalist id="blist" >#;

  my $DBNAME = "officedb";
  my $TABLE  = "third_party_payers";

  my $sql = "SELECT Third_Party_Payer_ID, BIN, Third_Party_Payer_Name  
               FROM $DBNAME.$TABLE 
              WHERE Status = 'Active'
                 && Primary_Secondary = 'Pri'
                 && BIN != '000000' 
           ORDER BY Third_Party_Payer_Name";

  my $sthx  = $dbx->prepare("$sql");
  $sthx->execute;

  while ( my ($TPP_ID, $TPP_BIN, $TPP_NAME) = $sthx->fetchrow_array() ) {
    print qq#<option value="$TPP_BIN - $TPP_NAME"> </option>\n#;
  }

  $sthx->finish;
  print qq# </datalist></td></tr>#;

  print qq#<tr><td>Status:</td><td><SELECT ID="status" NAME="status"><OPTION VALUE="yellow">Yellow</OPTION><OPTION VALUE="red">Red</OPTION></SELECT></td></tr>\n#;

  print qq#<tr><td>Problem:</td><td><INPUT ID="problem" TYPE="text" NAME="problem" SIZE=100 VALUE=""></td></tr>\n#;

  print qq#<td><INPUT style="padding:5px; margin:5px" TYPE="submit" NAME="save" VALUE="Save"><INPUT style="padding:5px; margin:5px" TYPE="button" NAME="Clear" VALUE="Clear" onclick="clearSearch(this.form);"></td><td>$nbsp</td></tr>\n#;

  print qq#</table>\n#;

  print "</FORM>\n";

  print qq#<br /><hr />\n#;

  print "<h2>Third Party Payer Issues</h2>\n";
    
  print qq#<link type="text/css" media="screen" rel="stylesheet" href="/includes/datatables/css/jquery.dataTables.css" /> \n#;
  print qq#<script type="text/javascript" charset="utf-8" src="/includes/datatables/js/jquery.dataTables.min.js"></script> \n#;
  print qq#<script type="text/javascript" charset="utf-8"> \n#;
  print qq#\$(document).ready(function() { \n#;
  print qq#                \$('\#tablef').dataTable( { \n#;
  print qq#                                "sScrollX": "100%", \n#;
  print qq#                                "bScrollCollapse": true,  \n#;
  print qq#                                "sScrollY": "300px", \n#;
  print qq#                                "bPaginate": false \n#;
  print qq#                } ); \n#;
  print qq#} ); \n#;
  print qq#</script> \n#;

  print qq#<table id="tablef">\n#;
  print "<thead>\n";
  print "<tr><th>Third Party Payer</th><th>BIN</th><th>Status</th><th>Problem</th><th>&nbsp</th></tr>\n";
  print "</thead>\n";
  print "<tbody>\n";

  my $sql = "SELECT a.BIN, b.Third_Party_Payer_Name, a.Problem, a.Status
              FROM reconrxdb.tpp_problems a
              JOIN officedb.third_party_payers b ON (a.BIN = b.BIN AND b.Status = 'Active')
          GROUP BY a.BIN";

#  print "$sql<br>";
 
  my $sthr = $dbx->prepare("$sql");
  $sthr->execute;

  while ( my ($bin, $tpp_name, $problem, $status) = $sthr->fetchrow_array() ) {
    $bin = sprintf( "%06d", $bin );
    print "<tr><td>$tpp_name</td><td>$bin</td><td>$status</td><td>$problem</td><td><INPUT TYPE='Button' NAME='Edit' VALUE='Edit' onClick=\"edit_record('$tpp_name', '$bin', '$status', '$problem')\">&nbsp<INPUT TYPE='Button' NAME='Remove' VALUE='Remove' onClick=\"remove_record('$bin')\"></td></tr>\n";
  }

  $sthr->finish();

  print '</tbody>';
  print "</table>\n";
}

#______________________________________________________________________________

sub update_table {
  my $sql = '';
  my $db = 'reconrxdb';
  my $tbl = 'tpp_problems';

  $bin = substr($bin,0,6);
  $problem =~ s/\'/\\'/g;

  if ( $sub_type =~ /Add/i ) {
    $sql = "INSERT INTO $db.$tbl VALUES ('$bin', '$status', '$problem')";
  }
  elsif ( $sub_type =~ /Update/i ) {
    $sql = "UPDATE $db.$tbl 
               SET Status = '$status',
                   Problem = '$problem'
             WHERE BIN = '$bin'";
  }
  elsif ( $sub_type =~ /Delete/i ) {
    $sql = "DELETE FROM $db.$tbl WHERE BIN = '$bin'";
  }

  my $sth = $dbx->prepare($sql);
  $sth->execute() or die $DBI::errstr;
  $retval = $sth->rows;

  if ( $retval != 1 ) {
    print "<span style='color: red'>Failed</span>";
  }

  $sth->finish();
}  

