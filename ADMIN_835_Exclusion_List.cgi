use File::Basename;

use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

$| = 1;
my $start = time();
($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";
$nbsp = "&nbsp;";
$blank = "&lt; blank &gt;";

my $AddRemoveElement;
my $AR_ID;
my $db_recon       = "reconrxdb";
my $tbl_exclusion  = "835setup_exclusions";
my $disabled = "disabled";

$ret = &ReadParse(*in);
&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

&readsetCookies;
&readThirdPartyPayers;
&readPharmacies;

$disabled = '' if ($USER =~ /66|69|72/);

#______________________________________________________________________________

if ( $USER ) {
    &MyReconRxHeader;
    &ReconRxHeaderBlock;
} else {
  &ReconRxGotoNewLogin;
  &MyReconRxTrailer;

  exit(0);
}

#______________________________________________________________________________

&hasAccess($USER);


#______________________________________________________________________________

# Create the inputfile format name
my ($min, $hour, $day, $month, $year) = (localtime)[1,2,3,4,5];
$year  += 1900;	# reported as "years since 1900".
$month += 1;	# reported ast 0-11, 0==January
$adate  = sprintf("%04d-%02d-%02d", $year, $month, $day);

($Title = $prog) =~ s/_/ /g;
print qq#<strong>$Title</strong>\n#;

$dbin    = "RIDBNAME";
$DBNAME  = $DBNAMES{"$dbin"};
$TABLE   = $DBTABN{"$dbin"};

my $dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
        { RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";

DBI->trace(1) if ($dbitrace);

#Start page operations
$AR_ID = $in{ar_id} if ($in{ar_id}); 

$AddRemoveElement = $in{AddRemoveElement} if ($in{AddRemoveElement}); 

&update_table if($AddRemoveElement);

&displayOptions;

#______________________________________________________________________________
# Close the Database

$dbx->disconnect;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub update_table {
  my $change;

  ($ar,$tpp_ncpdp) = split(':',$AddRemoveElement);

  if ($ar eq 'Remove' && $AR_ID) {
    $sql = "DELETE
              FROM $db_recon.$tbl_exclusion 
             WHERE TYPE = '$tpp_ncpdp' 
                && ID = $AR_ID
           ";
    $change = 1;
  
  }
  if ($ar eq 'Add' && $AR_ID) {
    $sql = "INSERT INTO $db_recon.$tbl_exclusion (TYPE,ID) 
             VALUES('$tpp_ncpdp','$AR_ID')
           ";
    $change = 1;
  }

  my $sthx  = $dbx->prepare("$sql");
  $sthx->execute if($change == 1);
}
 
sub displayOptions {
  print "<hr>\n";

  print qq#<style> \n#;
  print qq#td { border-top: none; }\n#;
  print qq#</style> \n#;
  print qq#<script type="text/javascript" charset="utf-8"> \n#;
  print qq# function AddRemove(act) { \n#;
  print qq# var alt1 = "Are you sure that you want to "\n#;
  print qq# alt1 += act\n#;
  print qq# alt1 += ' '\n#;
  print qq# if(act == 'Add') { var val =\$("\#AddNCPDP :selected").val(); var alt2 =  \$("\#AddNCPDP :selected").text();} else {var val =\$("\#RemoveNCPDP :selected").val(); var alt2 =  \$("\#RemoveNCPDP :selected").text();}\n#;
  print qq# var alt3 = alt1.concat(alt2)\n#;
  print qq#   if (confirm(alt3)) { document.getElementById('AddRemoveElement').value = act + ":NCPDP"; document.getElementById('ar_id').value = val; document.getElementById('addForm').submit();}else {} \n#;
  print qq# } \n#;
  print qq# function AddRemoveTPP(act) { \n#;
  print qq# var alt1 = "Are you sure that you want to "\n#;
  print qq# alt1 += act\n#;
  print qq# alt1 += ' '\n#;
  print qq# if(act == 'Add') { var val =\$("\#AddTPP :selected").val(); var alt2 =  \$("\#AddTPP :selected").text();} else {var val =\$("\#RemoveTPP :selected").val(); var alt2 =  \$("\#RemoveTPP :selected").text();}\n#;
  print qq# var alt3 = alt1.concat(alt2)\n#;
  print qq#   if (confirm(alt3)) { document.getElementById('AddRemoveElement').value = act + ":TPP"; document.getElementById('ar_id').value = val; document.getElementById('addForm').submit();}else {} \n#;
  print qq# } \n#;
  print qq#</script> \n#;

  print "<table>\n";

  my $db_office      = "officedb";
  my $tbl_pharmacy   = "pharmacy";

  print qq#<form id="addForm" action="$PROG" method="post" >#;
  print "<table>\n";
  
  my $sql = "SELECT TYPE,ID 
               FROM $db_recon.$tbl_exclusion 
           ORDER BY TYPE";

  my $sthx  = $dbx->prepare("$sql");
  $sthx->execute;

  while ( my ($TYPE,$ID) = $sthx->fetchrow_array() ) {
    push(@ncpdp,$ID) if ($TYPE eq "NCPDP");
    push(@tpp,$ID) if ($TYPE eq "TPP");
    $tpp{$ID} = 1;
  }

  $ncpdp_string = join(',', @ncpdp);
  $tpp_string   = join(',', @tpp);

  my $sql = "SELECT NCPDP 
               FROM $db_office.$tbl_pharmacy 
              WHERE status_reconrx = 'Active'
                && NCPDP NOT IN ($ncpdp_string)
           ORDER BY NCPDP";

  my $sthx  = $dbx->prepare("$sql");
  $sthx->execute;

  print qq#<tr><td style="width:450px"><INPUT style="padding:5px; margin:5px" TYPE="button"$disabled NAME="AddNCPDP" VALUE="Add NCPDP"onclick="AddRemove('Add');"></td>\n#;
  print qq#<td><select name="NCPDP" id="AddNCPDP" style="width:450px;">\n#;

  while ( my ($NCPDP) = $sthx->fetchrow_array() ) {
    $pharmacy_id = '';  
    $pharmacy_id =  $Reverse_Pharmacy_NCPDPs{$NCPDP};  
    print qq#<option value="$NCPDP">$NCPDP-$Pharmacy_Names{$pharmacy_id}</option>\n#;
  
  }
  print qq# </select></td></tr>#;

  print qq#<tr><td style="width:450px"><INPUT style="padding:5px; margin:5px" TYPE="button"$disabled NAME="RemoveNCPDP" VALUE="Remove NCPDP" onclick="AddRemove('Remove');"></td>\n#;
  print qq#<td><select name="RemoveNCPDP" id="RemoveNCPDP" style="width:450px;">\n#;

  foreach $ncpdp (@ncpdp) {
    $pharmacy_id = '';  
    $pharmacy_id =  $Reverse_Pharmacy_NCPDPs{$ncpdp};  
    print qq#<option value="$ncpdp">$ncpdp-$Pharmacy_Names{$pharmacy_id}</option>\n#;
  }
  print qq# </select></td></tr>#;
  print qq#<input type="hidden" name="AddRemoveElement" id="AddRemoveElement">\n#;
  print qq#<input type="hidden" name="ar_id" id="ar_id">\n#;
  print qq#</table>\n#;

  print qq#<hr>\n#;
  print "<table>\n";

  print qq#<tr><td style="width:450px"><INPUT style="padding:5px; margin:5px" TYPE="button"$disabled NAME="AddTPP" VALUE="Add TPP"onclick="AddRemoveTPP('Add');"></td>\n#;
  print qq#<td><select name="TPP" id="AddTPP" style="width:450px;">\n#;

  foreach $key (sort keys %ThirdPartyPayer_IDs) { 
    if($TPP_PriSecs{$key} eq 'Pri' && $Central_Pay_Entity{$key} eq 'No') {
      if (!$tpp{$key}) {
        print qq#<option value="$key">$key-$ThirdPartyPayer_Names{$key}</option>\n#;
      }
    }
  }

  print qq# </select></td></tr>#;
  print qq#<tr><td style="width:450px"><INPUT style="padding:5px; margin:5px" TYPE="button"$disabled NAME="RemoveTPP" VALUE="Remove TPP" onclick="AddRemoveTPP('Remove');"></td>\n#;
  print qq#<td><select name="RemoveTPP" id="RemoveTPP" style="width:450px;">\n#;

  foreach $tpp (@tpp) {
    print qq#<option value="$tpp">$tpp-$ThirdPartyPayer_Names{$tpp}</option>\n#;
  }
  print qq# </select></td></tr>#;
  print qq#</table>\n#;
  print qq#</form>\n#;
}
