require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

$| = 1;
my $start = time();
($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";
$nbsp = "&nbsp;";

my $DBase = 'reconrxdb';

&readsetCookies;
&readPharmacies;

#______________________________________________________________________________

if ( $USER ) {
  &MyReconRxHeader;
  &ReconRxHeaderBlock;
} else {
   &ReconRxGotoNewLogin;
   &MyReconRxTrailer;

   print qq#</BODY>\n#;
   print qq#</HTML>\n#;
   exit(0);
}

#______________________________________________________________________________


$dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
       { PrintError => 1, RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";
   
DBI->trace(1) if ($dbitrace);

&read_tpp_problems;

$ntitle = "Reconciling Third Party Payers";
print qq#<h1 class="page_title">$ntitle</h1>\n#;
&displayWebPage($PH_ID);

#______________________________________________________________________________

&MyReconRxTrailer;

$dbx->disconnect;

exit(0);

#______________________________________________________________________________

sub displayWebPage {
  
  my ($Pharmacy_ID) = @_;
  ##if ($Pharmacy_ID == 146 || $Pharmacy_ID == 931) {
  ##  $Pharmacy_ID = 792;
 ## }
  $DBase = 'Webinar' if($PH_ID == 4);

  print qq#<!-- displayWebPage -->\n#;

  ($PROG = $prog) =~ s/_/ /g;
  
  print qq#
  <div style="padding: 5px; background: \#5FC8ED; border: none; width: 380px; font-size: 16px;">
    <a href="/cgi-bin/EFT.cgi"><font color=white>Click here to submit request for ALL available EFT's</font></a>
  </div>
  \n#;

  print qq#<br /><table class="main">\n#;
  print qq#<tr valign=top><td class="multi_table">\n#;
  
  print qq#<table class="secondary">\n#;
  print qq#<tr><th colspan=3 class="align_left">Current Third Party Payers associated with $Pharmacy_Names{$dispNCPDP}</th></tr>\n#;
  print qq#<tr><th class="align_left">Third Party Payer</th>#;
  print qq#<th class="align_center">BIN</th>#;
  print qq#<th class="align_left">**Payment Cycle</th>#;
  print qq#<th class="align_center">ACH<br>Forms</th>#;
  print qq#</tr>\n#;
  
  $displaycount = 0;
	 
  #FROM SWITCH
  $sql = "
  SELECT a.tpp_id, b.Third_Party_Payer_Name, b.BIN, b.Payment_Cycle, b.Website, c.location
  FROM $DBase.tpp_list a
  LEFT JOIN officedb.third_party_payers b
  ON a.tpp_id = b.Third_Party_Payer_ID 
  LEFT JOIN reconrxdb.form_mst c
  ON (a.tpp_id = c.tpp_id AND c.Active = 1 AND c.form_type = 'EFT')
  WHERE Third_Party_Payer_Name IS NOT NULL
  AND a.Pharmacy_ID = $PH_ID
  ORDER BY b.Third_Party_Payer_Name
";
print "$sql\n" if( $PH_ID ==4);	 
  $sthrp = $dbx->prepare($sql);
  $sthrp->execute();
  my $numofrows = $sthrp->rows;

  while (my ($R_TPP_PRI, $Third_Party_Payer_Name, $BIN, $Payment_Cycle, $Website, $location) = $sthrp->fetchrow_array()) {
    next if ($BIN == 3858);   # Skip Express Script
    next if ($BIN == 610014); # Skip Medco
    next if ($BIN == 0);      # Skip Default All Inclusive

    $bgcolor = "green";
	
    if ($Website =~ /^\s*$/) {
      $Website = '';
    } elsif ($Website !~ /^HTTP/i) {
      $Website = "http://" . $Website;
    }

    if ($Problem_BIN{$BIN} !~ /^\s*$/) {
      $bgcolor = $Problem_Status{$BIN};
    }
	
    #Column: Third Party Payer
    print qq#<tr><td class="$bgcolor">#;
    if ($Problem_Problem{$BIN} !~ /^\s*$/) {
      print qq#<a href='\#' onclick='overlay$BIN()'><img src="/images/question.png" /></a> #;

      print qq#			 
      <div id="bin$BIN" class="overlay">
        <div>
          <p class="$bgcolor"><strong>$Third_Party_Payer_Name</strong></p>
          <p>$Problem_Problem{$BIN}</p>
          <p><a href='\#' onclick='overlay$BIN()'><strong>CLOSE</strong></a></p>
        </div>
      </div>
      #;

      print qq#
      <script>
        function overlay$BIN() {
          el = document.getElementById("bin$BIN");
          el.style.visibility = (el.style.visibility == "visible") ? "hidden" : "visible";
        }
      </script>
      #;
    }
	
    if ( $Website !~ /^\s*$/i ) {
      print qq#<a href="$Website" target="_blank">$Third_Party_Payer_Name</a>#;
    } else {
      print qq#$Third_Party_Payer_Name#;
    }

    print qq#</td>#;

	  #Column: BIN
    print qq#<td class="align_center $bgcolor" nowrap>$BIN</td>\n#;
	
	  #Column: Payment Cycle
    print qq#<td class="align_left $bgcolor">$Payment_Cycle</td>\n#;

	  #Column: ACH Form
    print qq#<td class="align_center $bgcolor" valign=middle>#;

    if ( $location =~ /_/ ) {
      print qq#<a href="../$location"><img src="/images/download.png" width="12" height="12" ></a> $nbsp#;
      $printed++;
    } 
    else {
      print qq#N/A $nbsp#;
    }
    print qq#</td>#;

    print qq#</tr>\n#;
		   
    $displaycount++;
  }
  $sthrp->finish;
	 
  if ( $displaycount ) {
    print qq#<tr><td colspan=4>**The above listed payment cycles were provided directly from the third party payers and apply to all of their plans (unless otherwise specified).</td></tr>\n#;
  } else {
    print qq#<tr><td colspan=4>No Third Party Payers associated with $Pharmacy_Names{$dispNCPDP} yet</td></tr>\n#;
  }
  
  print qq#</table>\n#;

  print qq#</td><td class="multi_table">\n#;
   
  print "$nbsp $nbsp $nbsp<br>\n";

  print qq#</td><td class="multi_table">\n#;
   
  print qq#<table class="secondary">\n#;
  print qq#<tr align=top><th colspan=2 class="align_center">Key</th></tr>\n#;
  print qq#<tr align=top><td style="border:1px solid black; background-color: \#000" height="50"><div class="stop_light red"></div></td> <td>Major Payment or Remit Issues</td></tr>\n#;
  print qq#<tr align=top><td style="border:1px solid black; background-color: \#000" height="50"><div class="stop_light yellow"></div></td> <td>Slow Payment -<br>Remit Issues</td></tr>\n#;
  print qq#<tr align=top><td style="border:1px solid black; background-color: \#000" height="50"><div class="stop_light green"></div></td> <td>No Payment or Remit Issues</td></tr>\n#;
  print qq#</table>\n#;
	 
  print qq#</td></tr>\n#;
  
  print qq#</table>\n#;
}

#______________________________________________________________________________

sub print_ACH_Setup_Form {
  my ($TPP_Name) = @_;

  print "sub print_ACH_Setup_Form: Entry. TPP_Name: $TPP_Name<br>\n" if ($debug);

  $webpath = qq#/WebShare/ACH_Setup_Forms/$TPP_Name#;
  $dskpath = "D:/WWW/members.recon-rx.com/WebShare/ACH_Setup_Forms/$TPP_Name";
# print "webpath: $webpath<br>\n";
# print "dskpath: $dskpath<br>\n";

  my $printed = 0;

  (@files) = &readfiles($dskpath);
  foreach $filename (sort {"\L$a" cmp "\L$b"} @files) {

     next if ( $filename =~ /Thumbs.db|\~$|.swp$/i );

     if ( $filename =~ /_/ ) {
        ($jdate, $rest) = split("_", $filename, 2);
     } else {
        $jdate = "";
        $rest  = $filename;
     }
   
     print "filename: $filename, jdate: $jdate<br>$nbsp rest: $rest<br>\n" if ($debug);

     print qq#<a href="$webpath/$filename"><img src="/images/download.png" width="12" height="12" ></a> $nbsp#;
     $printed++;
  }
  if ( !$printed ) {
     print qq#N/A $nbsp#;
  }

  print "sub print_ACH_Setup_Form: Exit.<br>\n" if ($debug);

}

#______________________________________________________________________________

sub read_tpp_problems {

# my $debug++;

  print "sub read_tpp_problems: Entry.<br>\n" if ($debug);

  my $DBNAME = "reconrxdb";
  $DBNAME = "webinar" if($PH_ID =~ /^23|4$/);
  my $TABLE  = "tpp_problems";

  my $sql = "
  SELECT LPAD(BIN, 6, 0) as BIN, Status, Problem 
  FROM $DBNAME.$TABLE
  ";

  print "sql:<br>$sql<br>\n" if ($debug);

  my $sthx  = $dbx->prepare("$sql");
  $sthx->execute;

  my $NumOfRows = $sthx->rows;
  print "Number of rows affected: $NumOfRows<br>\n" if ($debug);

  while ( my @row = $sthx->fetchrow_array() ) {

     my ($BIN, $Status, $Problem) = @row;

     $Problem_BINs{$BIN}++;
     $Problem_BIN{$BIN}      = $BIN;
     $Problem_Status{$BIN}   = $Status;
     $Problem_Problem{$BIN} = $Problem;

  }
  $sthx->finish;

  print "sub read_tpp_problems: Exit.<br>\n" if ($debug);

}

#______________________________________________________________________________
