use File::Basename;
use Time::Local;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

$| = 1;
my $start = time();
my ($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";
$nbsp = "&nbsp;";

$ret = &ReadParse(*in);
&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

$ptNCPDP    = $in{'ptNCPDP'};
$RADIO      = $in{'RADIO'};

#______________________________________________________________________________

&readsetCookies;

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


($title = $prog) =~ s/_/ /g;
$title =~ s/PCWNR/Post Check With No Remit/gi;
print qq#<strong>$title</strong><br>\n#;

#______________________________________________________________________________

$dbin     = "RXDBNAME";
$DBNAME   = $DBNAMES{"$dbin"};	"ReconRxDB";
$TABLE    = $DBTABN{"$dbin"};  	"planexceptions";
$FIELDS   = $DBFLDS{"$dbin"};
$FIELDS2  = $DBFLDS{"$dbin"} . "2";
$FIELDS3  = $DBFLDS{"$dbin"} . "2";
$fieldcnt = $#${FIELDS2} + 1;

%attr = ( PrintWarn=>1, RaiseError=>1, PrintError=>1, AutoCommit=>1, InactiveDestroy=>0, HandleError => \&handle_error );
$dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd, \%attr) || &handle_error;
   
DBI->trace(1) if ($dbitrace);

#______________________________________________________________________________

my ($ENV) = &What_Env_am_I_in;

$numberofhashes = 0;
$URL = "${prog}${ext}";
$FMT = "%0.02f";
$colspan = 9;
$subval  = "Submit";
$URLH    = "$prog.cgi";
$formnumber = 0;

&readPharmacies;
&readThirdPartyPayers;

$FirstTime = 0;

if ($RADIO =~ /^CheckNum/i ) {
   $CHECKEDCheckNum = "Checked";
} elsif ($RADIO =~ /^CheckAmt/i ) {
   $CHECKEDCheckAmt = "Checked";
} elsif ($RADIO =~ /^AmtNCPDP/i ) {
   $CHECKEDAmtNCPDP = "Checked";
} elsif ($RADIO =~ /^ALL/i ) {
   $CHECKEDALL      = "Checked";
} else {
   $CHECKEDNCPDP    = "Checked";
   $RADIO           = "AmtNCPDP";
   $FirstTime++;
}

undef $ptNCPDP if ( $RADIO !~ /NCPDP/i );

print qq#<table class="main">\n#;
print qq#<FORM ACTION="$URLH" METHOD="POST">\n#;
 
print qq#<tr valign=top>\n#;
print qq#<th colspan=$numberofhashes>Filter by:\n#;
#print qq# <INPUT TYPE="radio" NAME="RADIO" VALUE="NCPDP"    $CHECKEDNCPDP    onclick="this.form.submit();">NCPDP, \n#;
print qq# <INPUT TYPE="radio" NAME="RADIO" VALUE="ALL"      $CHECKEDALL      onclick="this.form.submit();">ALL\n#;
print qq# <INPUT TYPE="radio" NAME="RADIO" VALUE="CheckAmt" $CHECKEDCheckAmt onclick="this.form.submit();">Amount, \n#;
print qq# <INPUT TYPE="radio" NAME="RADIO" VALUE="AmtNCPDP" $CHECKEDAmtNCPDP onclick="this.form.submit();">Amount+NCPDP, \n#;
print qq# <INPUT TYPE="radio" NAME="RADIO" VALUE="CheckNum" $CHECKEDCheckNum onclick="this.form.submit();">Check\# \n#;
print qq#</th>\n#;
print qq#</tr>\n#;

if ($RADIO =~ /NCPDP/i ) {
   print qq#<tr><td colspan=$colspan>#;
   print qq#Pharmacy Select: \n#;
   print qq#<select name="ptNCPDP" onchange="this.form.submit()">\n#;
   foreach $Pharmacy_ID (sort { $Pharmacy_Names{$a} cmp $Pharmacy_Names{$b} } keys %Pharmacy_IDs) {
     next if ( $Pharmacy_Types{$Pharmacy_ID} !~ /ReconRx/i );
     print qq#<option #;
     print qq#selected="selected" # if ( $Pharmacy_ID == $ptNCPDP );
     print qq#value="$Pharmacy_ID">$Pharmacy_NCPDPs{$Pharmacy_ID} - $Pharmacy_Names{$Pharmacy_ID} #;
     print qq#</option>\n#;
   }
   print qq#</select>\n#;
   print qq#</td></tr>\n#;
#  print qq#<tr><th align=center colspan=&colspan><INPUT style="background-color:\#FF0; padding:5px; margin:5px" TYPE="Submit" NAME="Submit" VALUE="$subval"></th></tr>\n#;

}
print qq#</FORM>\n#;

print qq#<tr><th colspan=$numberofhashes></th></tr>\n#;

if ( !$FirstTime ) {
   &GatherDataPCWNR;
   &GatherDataPR;
   &DisplayData if ( !$FirstTime );
}

print "</table>\n";

#______________________________________________________________________________

# Close the Database

$dbx->disconnect;

#______________________________________________________________________________

for ($i=1;$i<=$formnumber;$i++) {

print <<JS;
<script type="text/javascript">

\$(document).ready(function() {
	\$("#matchForm${i}").submit(function() {
      if ( \$("input[name='YELLOW']").is(':checked') ) {
		\$.ajax({
			type: "POST",
			url: '/cgi-bin/ADMIN_PCWNR_Posting_Tool_sub.cgi',
			data: \$("#matchForm${i}").serialize(), // serializes the form's elements.
			success: function(data)
			{
			   // alert(data);
               \$(".hideme${i}").hide();
               \$(".updateme${i}").html('<td colspan=$numberofhashes>'+data+'</td>');
			},
            error: function(XMLHttpRequest, textStatus, errorThrown) { 
                alert("Status: " + textStatus);
                alert("Error2: " + errorThrown); 
                alert("Error:"   + error); 
            }
		});
		return false; // avoid to execute the actual submit of the form.
      } else {
		return false; 
      }
	});
	
});
</script>
JS

}

#______________________________________________________________________________

my $end = time();
$elapsed = $end - $start;
print "<hr>Time elapsed: $elapsed seconds<hr>\n";

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub GatherDataPCWNR {
  $dbin    = "RNDBNAME";
  $DBNAME  = $DBNAMES{"$dbin"};
  $TABLE   = $DBTABN{"$dbin"};
  $FIELDS  = $DBFLDS{"$dbin"};
  $FIELDS2 = $DBFLDS{"$dbin"} . "2";
  
  #______________________________________________________________________________

  %NCPDPs       = ();
  %PharmNames   = ();
  %TPPs         = ();
  %CheckNumbers = ();
  %CheckAmounts = ();
  %CheckDates   = ();
  %DateAddeds   = ();
  %PaymentTypes = ();
  %FLAGs        = ();
  $numberofhashes = 8;
  
  $sql  = "SELECT NCPDP, DateAdded, BIN, ThirdParty, PaymentType, CheckNumber,
                  CheckAmount, CheckDate, CheckReceivedDate
             FROM $DBNAME.$TABLE 
            WHERE (1=1) ";
  $sql .= "    && Pharmacy_ID = $ptNCPDP " if ($ptNCPDP !~ /^\s*$/i );
  $sql .= "    && NCPDP NOT IN ('1111111', '2222222') " if ($ENV !~ /DEV/i );
  $sql .= "ORDER BY NCPDP, ThirdParty, PaymentType";
  
  ($sqlout = $sql) =~ s/\n/<br>\n/g;
  
  $sthx = $dbx->prepare($sql);
  $sthx->execute();
  
  my $NumOfRows = $sthx->rows;
  
  if ( $NumOfRows > 0 ) {
    while ( my ( $NCPDP, $DateAdded, $BIN, $ThirdParty, $PaymentType, $CheckNumber, $CheckAmount, $CheckDate, $CheckReceivedDate) = $sthx->fetchrow_array() ) {
       $NCPDP = substr("0000000" . $NCPDP, -7);
       $PharmName = $Pharmacy_Names{$NCPDP};
       my $FLAG = "";
       if ( $PaymentType =~ /CHK/i && $CheckNumber =~ /^\s*$/ ) {
          $FLAG .= "Fix CheckNumber. ";
       }
       if ( $CheckDate =~ /\\./ || $CheckDate < 20100000 || $CheckDate > 20200000 || $CheckDate !~ /^\s*20/ ) {
          $FLAG .= "Fix CheckDate. ";
       }
       if ( $CheckNumber =~ /\// ) {
          $FLAG .= "Fix CheckNumber. ";
       }

       my $OCheckAmount = "\$" . &commify(sprintf("$FMT", $CheckAmount));
       $key = "$NCPDP##$CheckNumber##$CheckAmount";

       $NCPDPs{$key}       = $NCPDP;
       $PharmNames{$key}   = $PharmName;
       $TPPs{$key}         = $ThirdParty;
       $CheckNumbers{$key} = $CheckNumber;
       $CheckAmounts{$key} = $OCheckAmount;
       $CheckDates{$key}   = $CheckDate;
       $DateAddeds{$key}   = $DateAdded;
       $PaymentTypes{$key} = $PaymentType;
       $FLAGs{$key}        = $FLAG;
    }
  } else {
    print "No entries found!<br>\n";
  }
  
  $sthx->finish;
}

#______________________________________________________________________________

sub GatherDataPR {
  my $dbin     = "R8DBNAME";
  my $DBNAME   = $DBNAMES{"$dbin"};
  my $TABLE    = 'Checks';
  my $FIELDS   = $DBFLDS{"$dbin"};
  my $FIELDS2  = $DBFLDS{"$dbin"} . "2";
  my $fieldcnt = $#${FIELDS2} + 2;
  
  $TOTAL  = 0;

  my $sql = "SELECT R_TPP, R_TS3_NCPDP, R_BPR04_Payment_Method_Code, R_BPR02_Check_Amount, R_BPR03_CreditDebit_Flag_Code, R_BPR16_Date, 
                    R_TRN02_Check_Number, R_PENDRECV, R_Seen, R_CheckReceived_Date, R_ISA06_Interchange_Sender_ID, R_PostedBy
               FROM $DBNAME.$TABLE
              WHERE (R_CheckReceived_Date IS NULL || R_CheckReceived_Date='0000-00-00') ";
  $sql .= "    && Pharmacy_IDP = $ptNCPDP " if ($ptNCPDP !~ /^\s*$/i );
  $sql .= "    && R_TS3_NCPDP NOT IN ('1111111', '2222222') " if ($ENV !~ /DEV/i );
  $sql .= "ORDER BY R_PENDRECV DESC, R_TPP";

  ($sqlout = $sql) =~ s/\n/<br>\n/g;
 
  my $stb = $dbx->prepare($sql);
  my $numofrows = $stb->execute;

  if ( $numofrows <= 0 ) {
     print "No records found for this date<br>\n";
  } else {

    while (my @row = $stb->fetchrow_array()) {
       ($R_TPP, $R_TS3_NCPDP, $R_BPR04_Payment_Method_Code, $R_BPR02_Check_Amount, $R_BPR03_CreditDebit_Flag_Code, $R_BPR16_Date, $R_TRN02_Check_Number, $R_PENDRECV, $R_Seen, $R_CheckReceived_Date, $R_ISA06_Interchange_Sender_ID, $R_PostedBy) = @row;

       my $Was_me = "";
       my $Use_me = "";

       $Was_me = $R_TPP;
       $Use_me = $TPP_Names{ $Reverse_ISA_IDs{$R_ISA06_Interchange_Sender_ID} };

       if ( $Was_me ne $Use_me ) {
       } else {
          $Use_me = $Was_me;
       }
       $Use_me = $Was_me if ( $Use_me =~ /^\s*$/ );
       
#------------------------------------------------------

       next if ( $ptNCPDP > 0 && $R_TS3_NCPDP != $ptNCPDP );

       $key = "$R_TPP##$R_BPR04_Payment_Method_Code##$R_TRN02_Check_Number##$R_BPR02_Check_Amount##$R_BPR16_Date##$R_PENDRECV##$R_Seen##$R_CheckReceived_Date##$R_ISA06_Interchange_Sender_ID##$R_PostedBy##$Use_me##$R_TS3_NCPDP";

       $rec1{$key} = "$R_PENDRECV";
       $rec2{$key} = "$Use_me##$R_TRN02_Check_Number";
    }
  }
  $stb->finish();

  print qq#sub GatherDataPR. Exit.<hr size=8 color=red>\n# if ($debug);
}

#______________________________________________________________________________

sub DisplayData {
  @hashes = ("NCPDPs", "PharmNames", "TPPs", "CheckNumbers", "CheckAmounts", "CheckDates", "DateAddeds", "FLAGs");

  $linesprinted = 0;
  $formnumber   = 0;

  &print_headers;

  $foundcount0  = 0;

# sort by NCPDP, TPP, then Check Amounts

  foreach $Okey (sort {
      $NCPDPs{$a} <=> $NCPDPs{$b} ||
      $TPPs{$a} cmp $TPPs{$b} ||
      $CheckAmounts{$a} <=> $CheckAmounts{$b}
    } keys %NCPDPs) {

    $foundcount0++;
#   next if ( $foundcount0 > 20 && $testing );

    print qq#<tr><th colspan=$colspan><hr size=4 noshade color="black"></th></tr>\n#;

#   print the "WHITE Line"

    $YELLOW  = "";
    $WHITE   = "";
    $YELLOWCNT = 0;
    $formnumber++;
    print qq#<FORM id="matchForm${formnumber}">\n#;
  
    print qq#<tr class="updateme${formnumber}">#;
    print qq#<td><input type="submit" value="Post/Arch" class="button-form"></td>\n#;
    foreach $hash (@hashes) {
       $val = $$hash{$Okey};
#      print "<hr>hash: $hash, val: $val<br>\n";
       if ( $hash =~ /Check/i ) {
          $ALIGN = qq#align="right"#;
       } elsif ( $hash =~ /FLAG/i ) {
          $ALIGN = qq#colspan=2#;
       } else {
          $ALIGN = "";
       }
       print "<td $ALIGN>$val</td>";
       $WHITE .= "$val##";
    }
    print "</tr>\n";
#   print "<tr><td $ALIGN>1. $WHITE</td></tr>";
    $val = $PaymentTypes{$Okey};
#   print "Payment Type: $val<br>\n";
    $WHITE .= "$val##";
    $WHITE =~ s/##\s*$//g;
#   print "<tr><td $ALIGN>2. $WHITE</td></tr>";

    print qq#<INPUT TYPE="hidden" NAME="WHITE" VALUE="$WHITE">\n#;
    print qq#<INPUT TYPE="hidden" NAME="USER"  VALUE="$USER">\n#;
    print qq#<INPUT TYPE="hidden" NAME="OWNER" VALUE="$OWNER">\n#;
    $linesprinted++;
    $CHECKNUMBER = $CheckNumbers{$Okey};
    $CHECKAMOUNT = $CheckAmounts{$Okey};
    $CHECKAMOUNT =~ s/\$|,//g;
    $foundcount = 0;

# Compare $NCPDPs{$key} to $R_TS3_NCPDP

    foreach $key (sort { $rec1{$b} cmp $rec1{$a} || $rec2{$a} cmp $rec2{$b} } keys %rec2) {
       ($R_TPP, $R_BPR04_Payment_Method_Code, $R_TRN02_Check_Number, $R_BPR02_Check_Amount,
        $R_BPR16_Date, $R_PENDRECV, $R_Seen, $R_CheckReceived_Date,
        $R_ISA06_Interchange_Sender_ID, $R_PostedBy, $Use_me, $R_TS3_NCPDP) = split("##", $key);

       $R_TS3_NCPDP = substr("0000000" . $R_TS3_NCPDP, -7);

       if ($RADIO =~ /^CheckNum/i ) {

          ($TRN02 = $R_TRN02_Check_Number) =~ s/^\0+//g;
          next if ( $CHECKNUMBER =~ /^\s*$/ ||
                    $CHECKNUMBER == 0       ||
                   ($CHECKNUMBER !~ /^$TRN02$/i &&
                    $CHECKNUMBER != $TRN02
                   )
                  );
          if ( $debug ) {
             print "CHECKNUMBER: $CHECKNUMBER<br>\n";
             print "R_TRN02_Check_Number: $R_TRN02_Check_Number<hr>\n";
          }

       } elsif ($RADIO =~ /^CheckAmt/i ) {
          next if ( $CHECKAMOUNT != $R_BPR02_Check_Amount );
       } elsif ($RADIO =~ /^AmtNCPDP/i ) {
          next if ( $ptNCPDP > 0 && $R_TS3_NCPDP != $ptNCPDP );
          next if ( $CHECKAMOUNT != $R_BPR02_Check_Amount );
       } elsif ($RADIO =~ /^ALL/i ) {
          next if ( $R_TS3_NCPDP != $NCPDPs{$Okey} );
       }
       next if ( $R_BPR02_Check_Amount == 0.00 );	# jlh. 11/20/2014. Tori

       $foundcount++;

#      next if ( $foundcount > 10 && $testing );

       $TOTAL += $R_BPR02_Check_Amount;
       my $OcheckAmount = "\$" . &commify(sprintf("$FMT", $R_BPR02_Check_Amount));
  
       my $jdate = $R_BPR16_Date;
       my $year  = substr($jdate, 0, 4);
       my $mon   = substr($jdate, 4, 2);
       my $mday  = substr($jdate, 6, 2);
       my $sec   = 0; $min = 0; $hour = 0;
       my $mon1  = $mon;
       my $mon   = $mon - 1;
  
       my $pendrecvname = "PENDRECV##" . "$key";
       if      ( $R_PENDRECV =~ /^P/i ) {
          $PRVAL = "Pending";
       } elsif ( $R_PENDRECV =~ /^R/i ) {
          $PRVAL = "Received";
       } else {
          $PRVAL = "";
       }

       $addcolor    = "yellow";
  	   
       if ($R_PostedBy =~ /recon/i) {
          $R_PostedByTD = '<img src="/images/reconrx16px.png">';
       } else {
          $R_PostedByTD = '<div style="min-width: 16px;"></div>';
       }

       $YELLOW = "$R_TS3_NCPDP##$R_TRN02_Check_Number##$R_BPR02_Check_Amount##$R_BPR16_Date##$Use_me";
       $YELLOWCNT++;
       print qq#<tr class="hideme${formnumber}">#;
       print qq#<td align=center><INPUT TYPE="radio" NAME="YELLOW" VALUE="$YELLOW"></td>\n#;
       print qq#<td class="$addcolor">$R_TS3_NCPDP</td>#;
       print qq#<td class="$addcolor">$Pharmacy_Names{$R_TS3_NCPDP}</td>#;
       print qq#<td class="$addcolor">$Use_me</td>#;
       print qq#<td class="align_right $addcolor">$R_TRN02_Check_Number</td>#;
       print qq#<td class="align_right $addcolor">$OcheckAmount</td>#;
       print qq#<td class="align_right $addcolor">$R_BPR16_Date</td>#;	# Was $Odate
       print qq#<td class="$addcolor">$PRVAL</td>#;
       print qq#<td class="$addcolor">$R_Seen</td># if ($debug);
       print qq#<td class="$addcolor">$R_PostedByTD</td>#;
       print qq#</tr>\n#;

       $linesprinted++;
       if ( $linesprinted > 10 ) {
          $linesprinted = 0;
       }
    }

    if ( $foundcount <= 0 ) {
       print qq#<tr><th colspan=$colspan class="grey">No matches found</th></tr>\n#;
    }

    print qq#<tr><th colspan=$colspan class="grey">YELLOWCNT: $YELLOWCNT</th></tr>\n# if ($debug);
    print qq#<INPUT TYPE="hidden" NAME="YELLOWCNT" VALUE="$YELLOWCNT">\n#;
    print qq#</FORM>\n#;
  }
}

#______________________________________________________________________________

sub print_headers {
  print qq#<tr><th colspan=$colspan><hr size=4 noshade color="black"></th></tr>\n#;
  print "<tr>";
  print "<th>$nbsp</th>";
  foreach $hash (@hashes) {
    ($hashname =  $hash) =~ s/s$//;
    $hashname =~ s/Number/#/gi;
    $hashname =~ s/Check/Chk/gi;
    $hashname =~ s/Amount/Amt/gi;
    $hashname =~ s/PharmName/Name/gi;
    $hashname =~ s/DateAdded/Added/gi;
    print "<th align=left>$hashname</th>";
    $linesprinted++;
  }
  print "</tr>\n";
}

#______________________________________________________________________________
