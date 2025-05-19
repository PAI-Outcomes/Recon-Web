require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Time::Local;
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);
use PDF::API2;
use PDF::API2::Content;
use Excel::Writer::XLSX;
use LWP::Simple;
use Date::Format;

$| = 1;
my $start = time();
my ($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";
$nbsp  = "&nbsp;";

$ret = &ReadParse(*in);

&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

$SRC         = $in{'SRC'};
$DB          = $in{'DB'};
$Payer_ID    = $in{'Payer_ID'};
$FTYPE       = $in{'FTYPE'};
$Check_ID    = $in{'Check_ID'};
$CHKDATE     = $in{'CHKDATE'};
$CHKNUM      = $in{'CHKNUM'};
$TPPPRI      = $in{'TPPPRI'};
$PostedBy    = $in{'PostedBy'};
$DISPTPPID   = $in{'DISPTPPID'};
$DISPonRemit = $in{'DISPonRemit'};
$DISPCHKAMT  = $in{'DISPCHKAMT'};

#______________________________________________________________________________

&readsetCookies;
&readPharmacies();

#______________________________________________________________________________

if ( $USER ) {
  &MyReconRxHeader;
  if ( $PH_ID  eq 'Aggregated') {
    &ReconRxAggregatedHeaderBlock_New;
  }
  else {
    &ReconRxHeaderBlock;
  }
} else {
   &ReconRxGotoNewLogin;
   &MyReconRxTrailer;

   print qq#</BODY>\n#;
   print qq#</HTML>\n#;
   exit(0);
}
my $agg_check;
if ( $PH_ID  eq 'Aggregated') {
  $agg_check = 1;
  $PH_ID = $Agg_String;
}

#______________________________________________________________________________
# Create the inputfile format name
my ($min, $hour, $day, $month, $year) = (localtime)[1,2,3,4,5];
$year  += 1900;	# reported as "years since 1900".
$month += 1;	# reported ast 0-11, 0==January
$syear  = sprintf("%4d", $year);
$smonth = sprintf("%02d", $month);
$sday   = sprintf("%02d", $day);
$tdate  = sprintf("%04d/%02d/%02d", $year, $month, $day);
$ttime  = sprintf("%02d:%02d", $hour, $min);
$mydate = sprintf("%02d/%02d/%04d %02d:%02d", $month, $day, $year, $hour, $min);
#______________________________________________________________________________

my ($ENV) = &What_Env_am_I_in;

$outdir = qq#D:\\WWW\\members.recon-rx.com\\Webshare\\Reports#;

$leftmargin =  20;
$ytop       = 840;
$pagenum    =   1;
$colwidth   =  60;
%font       =  ();
$TPPID      =  "";
$FMT = "%0.02f";
@abbr = qw( Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec );

#______________________________________________________________________________
#
my $TABLE    = $DBTABN{"$dbin"};

my $R8dbin   = "R8DBNAME";
my $R8DBNAME = $DBNAMES{"$R8dbin"};
my $R8TABLE  = $DBTABN{"$R8dbin"};

my $P8dbin   = "P8DBNAME";
my $P8DBNAME = $DBNAMES{"$P8dbin"};
my $P8TABLE  = $DBTABN{"$P8dbin"};

my $FIELDS   = $DBFLDS{"$R8dbin"};
my $FIELDS2  = $DBFLDS{"$R8dbin"}. "2";
my $fieldcnt = $#${FIELDS2}+ 2;

my $check_tbl = 'checks';

if ($PH_ID == 11 || $PH_ID == 23 || $PH_ID eq "11,23") {
	$R8DBNAME = "webinar";
	$P8DBNAME = "webinar";
}

#______________________________________________________________________________
 
%attr = ( PrintWarn=>1, RaiseError=>1, PrintError=>1, AutoCommit=>1, InactiveDestroy=>0, HandleError => \&handle_error );
$dbx = DBI->connect("DBI:mysql:$R8DBNAME:$DBHOST",$dbuser,$dbpwd, \%attr) || &handle_error;
DBI->trace(1) if ($dbitrace);

&readThirdPartyPayers;
&read_Other_Sources_835s;
&read_Other_Sources_835s_Lookup;

$TPPPRINAME          = $TPP_Names{$TPPPRI};
$TPP                 = $TPP_Names{$Payer_ID};
$Trans_Fee_Loc       = $TPP_Trans_Fee_Locs{$Payer_ID};
$Trans_Fee_Loc_Chk   = $TPP_Trans_Fee_Locs_PSAO{$Payer_ID};
$DIR_Loc             = $TPP_DIR_Locs{$Payer_ID};
$DIR_Loc_Chk         = $TPP_DIR_Locs_PSAO{$Payer_ID};
$DIR_Loc_Display     = $TPP_DIR_Locs_Display{$Payer_ID} if($TPP_DIR_Locs_Display{$Payer_ID});
$Tax_Location        = $TPP_Tax_Locations{$Payer_ID};
$LA_Provider_Fee_Loc = $TPP_LA_Provider_Fee_Locs{$Payer_ID};

&displayWebPage;

$dbx->disconnect;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayWebPage {
  print qq#<!-- displayWebPage -->\n#;

  print qq#<a href="javascript:history.go(-1)">Return</a><br>\n#;

  my ($mon, $mday, $year) = split('\/', $CHKDATE);

  $dispdate2 = sprintf("%04d%02d%02d",   $year, $mon, $mday);
  ($PROG = $prog) =~ s/_/ /g;

#  print "DATE: $dispdate2 ($mon, $mday, $year)<br>";

  $NamePDF = "${CHKNUM}.pdf";
  $NameSS  = "${CHKNUM}.xlxs";
  $Name835 = "${CHKNUM}.txt";

  if ($PostedBy =~ /recon/i) {
    $PostedBy_Display = qq#ReconRx <img src="/images/reconrx16px.png" />#;
  } elsif ($PostedBy !~ /^\s*$/) {
    $PostedBy_Display = $Pharmacy_Name;
  } else {
    $PostedBy_Display = "Not Recorded";
  }
  
  print qq#<table>\n#;
  print qq#<tr><th class="align_left" colspan=3><h1 class="page_title">Retrieve Remit</h1></th></tr>#;

  print qq#<tr><th class="align=left">Payer:        </th><th colspan=2><font style="BACKGROUND-COLOR: yellow">$TPP_Names{$TPPPRI}#;

  if ( $TPPPRI != $Payer_ID ) {
     print qq#:<br>- $TPP_Names{$Payer_ID}#;
  }

  print qq#</font></th></tr>\n#;
  print qq#<tr><th class="align=left">Check Number: </th><th colspan=2><font style="BACKGROUND-COLOR: yellow">$CHKNUM</font></th></tr>\n#;
  print qq#<tr><th class="align=left">Check Date:   </th><th colspan=2><font style="BACKGROUND-COLOR: yellow">$CHKDATE</font></th></tr>\n#;
  print qq#<tr><th class="align=left">Check Amount: </th><th colspan=2><font style="BACKGROUND-COLOR: yellow">$DISPCHKAMT</font></th></tr>\n#;
  print qq#<tr><th class="align=left">Posted By: </th><th colspan=2>$PostedBy_Display</th></tr>\n#;
  print qq#<tr><th class="align_center" colspan=3><i>Click on the file type for the format you want to retrieve</i></th></tr>#;
  print qq#<tr><td class="align_center" colspan=3><i>Report may take several seconds to generate</i></td></tr>#;
  print qq#<tr>#;

  print qq#<td class="align_center" colspan=1 width=33%>\n#;
  $URLH = "Retrieve_Remit.cgi";
  print qq#<FORM ACTION="$URLH" METHOD="POST" onsubmit="return validate(this)\;">\n#;
  print qq#<INPUT TYPE="hidden" NAME="SRC"        VALUE="$SRC">\n#;
  print qq#<INPUT TYPE="hidden" NAME="FTYPE"      VALUE="PDF">\n#;
  print qq#<INPUT TYPE="hidden" NAME="Check_ID"   VALUE="$Check_ID">\n#;
  print qq#<INPUT TYPE="hidden" NAME="Payer_ID"   VALUE="$Payer_ID">\n#;
  print qq#<INPUT TYPE="hidden" NAME="TPPPRI"     VALUE="$TPPPRI">\n#;
  print qq#<INPUT TYPE="hidden" NAME="CHKNUM"     VALUE="$CHKNUM">\n#;
  print qq#<INPUT TYPE="hidden" NAME="CHKDATE"    VALUE="$CHKDATE">\n#;
  print qq#<INPUT TYPE="hidden" NAME="REF02_STR"  VALUE="$str_ref02">\n#;
  print qq#<INPUT TYPE="hidden" NAME="PostedBy"   VALUE="$PostedBy">\n#;
  print qq#<INPUT TYPE="hidden" NAME="DISPCHKAMT" VALUE="$DISPCHKAMT">\n#;
  print qq#<INPUT style="padding:5px; margin:5px" TYPE="Submit" NAME="Submit" VALUE="PDF">\n#;
  print qq#</FORM>\n#;
  print qq#</td>\n#;

  print qq#<td class="align_center" colspan=1 width=33%>\n#;
  $URLH = "Retrieve_Remit.cgi";
  print qq#<FORM ACTION="$URLH" METHOD="POST" onsubmit="return validate(this)\;">\n#;
  print qq#<INPUT TYPE="hidden" NAME="SRC"        VALUE="$SRC">\n#;
  print qq#<INPUT TYPE="hidden" NAME="FTYPE"      VALUE="SS">\n#;
  print qq#<INPUT TYPE="hidden" NAME="Check_ID"   VALUE="$Check_ID">\n#;
  print qq#<INPUT TYPE="hidden" NAME="Payer_ID"   VALUE="$Payer_ID">\n#;
  print qq#<INPUT TYPE="hidden" NAME="TPPPRI"     VALUE="$TPPPRI">\n#;
  print qq#<INPUT TYPE="hidden" NAME="CHKNUM"     VALUE="$CHKNUM">\n#;
  print qq#<INPUT TYPE="hidden" NAME="CHKDATE"    VALUE="$CHKDATE">\n#;
  print qq#<INPUT TYPE="hidden" NAME="REF02_STR"  VALUE="$str_ref02">\n#;
  print qq#<INPUT TYPE="hidden" NAME="PostedBy"   VALUE="$PostedBy">\n#;
  print qq#<INPUT TYPE="hidden" NAME="DISPCHKAMT" VALUE="$DISPCHKAMT">\n#;
  print qq#<INPUT style="padding:5px; margin:5px" TYPE="Submit" NAME="Submit" VALUE="Spreadsheet">\n#;
  print qq#</FORM>\n#;
  print qq#</td>\n#;

  my ($my835Filename) = &set835($Check_ID);

  if ( $TPPPRI == $Payer_ID ) {
     if ( $Pharmacy_Wants835Files{$PH_ID} =~ /^Y/i ) {
        print qq#<td class="align_center" colspan=1 width=33%>\n#;
        $URLH = "Retrieve_Remit.cgi";
        print qq#<FORM ACTION="$URLH" METHOD="POST" onsubmit="return validate(this)\;">\n#;
        print qq#<INPUT TYPE="hidden" NAME="FTYPE"      VALUE="835">\n#;
        print qq#<INPUT TYPE="hidden" NAME="Check_ID"   VALUE="$Check_ID">\n#;
        print qq#<INPUT TYPE="hidden" NAME="Payer_ID"   VALUE="$Payer_ID">\n#;
        print qq#<INPUT TYPE="hidden" NAME="TPPPRI"     VALUE="$TPPPRI">\n#;
        print qq#<INPUT TYPE="hidden" NAME="CHKNUM"     VALUE="$CHKNUM">\n#;
        print qq#<INPUT TYPE="hidden" NAME="CHKDATE"    VALUE="$CHKDATE">\n#;
        print qq#<INPUT TYPE="hidden" NAME="REF02_STR"  VALUE="$str_ref02">\n#;
        print qq#<INPUT TYPE="hidden" NAME="PostedBy"   VALUE="$PostedBy">\n#;
        print qq#<INPUT TYPE="hidden" NAME="DISPCHKAMT" VALUE="$DISPCHKAMT">\n#;
        print qq#<INPUT style="padding:5px; margin:5px" TYPE="Submit" NAME="Submit" VALUE="835">\n#;
        print qq#</FORM>\n#;
        print qq#</td>\n#;
     } else {
        print qq#<td class="align_center" colspan=1 width=33%>$nbsp</td>#;
     }
  } else {
     print qq#<td class="align_center" colspan=1 width=33%>835 (N/A)<br>$TPPPRINAME</td>#;
  }

  print qq#</tr>\n#;

  if ( $Pharmacy_Wants835Files{$PH_ID} !~ /^Y/i ) {
     print qq#<tr><td colspan=3><i>If you want to download actual 835 remits, please contact us.</i></td></tr>#;
  }

  if ( $FTYPE =~ /^PDF$|^SS$|^835$/i ) {
    &genreport($FTYPE, $Check_ID, $Payer_ID);
  } elsif ( $FTYPE ) {
  ##  print qq#<tr><td>Unknown file type selected!</td></tr>\n#;
  }

  print qq#</table>\n#;
}

#______________________________________________________________________________

sub setPDF {
  my ($PDFName) = @_;

#  my $picture = "images/ReconRx-Retrieve.jpg";
  ##my $picture = "images/ReconRX_Logo_Grey_bg.jpg";
  my $picture = "images/Outcomes_ReconRx.jpg";

  unlink "$PDFName" if ( -e "$PDFName" );

  $title = qq#ReconRx: Retrieve Remit for $TPP - Check: $CHKNUM, $DISPCHKAMT, $CHKDATE#;

  $pdf  = PDF::API2->new(-file => "$PDFName");
  %font = (
      Helvetica => {
          Bold   => $pdf->corefont( 'Helvetica-Bold',    -encoding => 'latin1' ),
          Roman  => $pdf->corefont( 'Helvetica',         -encoding => 'latin1' ),
          Italic => $pdf->corefont( 'Helvetica-Oblique', -encoding => 'latin1' ),
      },
      Times => {
          Bold   => $pdf->corefont( 'Times-Bold',   -encoding => 'latin1' ),
          Roman  => $pdf->corefont( 'Times',        -encoding => 'latin1' ),
          Italic => $pdf->corefont( 'Times-Italic', -encoding => 'latin1' ),
      },
  );


  $xloc = $leftmargin;
  $yloc = $ytop - 100;

  # Define page sizes
  $page = $pdf->page;		# Create a page
  $page->mediabox ('A4');
  $page->cropbox ('A4');

  # Create some Fonts
  # $font = $pdf->corefont('Arial',-encode => 'latin1');

  %h = $pdf->info(
          'Author'       => "PAIT",
          'CreationDate' => "$mydate",
          'ModDate'      => "$mydate",
          'Creator'      => "$prog",
          'Producer'     => "PDF::API2",
          'Title'        => "$title",
          'Subject'      => "Retrieve Remit",
          'Keywords'     => "ReconRx"
  );

  my $scale = 0.85;
  my $photo = $page->gfx;
  die("Unable to find image file: $!") unless -e "$picture";
  my $photo_file = $pdf->image_jpeg($picture);
  $photo->image( $photo_file, $xloc, $yloc, $scale);
  $yloc = $yloc - 16;

  &print_Heading_Line;
}

#______________________________________________________________________________

sub setExcel {
  my ($SSName) = @_;

  $headformat = "";
  $format     = "";
  $dolformat  = "";

  unlink "$SSName" if ( -e "$SSName" );

  $workbook  = Excel::Writer::XLSX->new("$SSName");
  $worksheet = $workbook->add_worksheet();

  foreach $worksheet ($workbook->sheets()) {
     $worksheet->set_landscape();
     $worksheet->fit_to_pages( 1, 0 ); # Fit all columns on a single page
     $worksheet->hide_gridlines(0);    # 0 = Show gridlines
     $worksheet->freeze_panes( 1, 0 ); # Freeze first row
     $worksheet->repeat_rows( 0 );     # Print on each page
  }

  $TITLE = qq#$Pharmacy_Name ($USER)\nReconRx: Retrieve Remit for $TPP - Check: $CHKNUM, $DISPCHKAMT, $CHKDATE#;

  $worksheet->set_header("&C\&11\&\"Calibri,Regular\"$TITLE", 0.20);
  $worksheet->print_area('A:H' );

  $worksheet->set_footer("\&L&D\&RPage &P of &N");
  $worksheet->repeat_rows(0);
  $worksheet->set_margin_left(0.20);
  $worksheet->set_margin_right(0.20);

  $workbook->set_properties(
      title    => "$report",
      author   => "ReconRx - PAIIT",
      comments => "Created with Perl and Excel::Writer::XLSX\n$tdate $ttime",
      subject  => "$report"
  );

  $headformat = $workbook->add_format(bold => 1, color => 'red', font =>'Arial', align => 'left');
  $headformat->set_align('top');
  $headformat->set_text_wrap();

  $headformatL= $workbook->add_format(bold => 1, color => 'red', font =>'Arial', align => 'left');
  $headformatL->set_text_wrap();

  $headformatR= $workbook->add_format(bold => 1, color => 'red', font =>'Arial', align => 'right');
  $headformatR->set_text_wrap();

  $headformatC= $workbook->add_format(bold => 1, color => 'red', font =>'Arial', align => 'center');
  $headformatC->set_text_wrap();

  $headformatD= $workbook->add_format(bold => 1, color => 'red', font =>'Arial', align => 'right', num_format => '$#,##0.00');
  $headformatD->set_text_wrap();

  $headformatI= $workbook->add_format(bold => 1, bg_color => 'cyan', font =>'Arial', align => 'left');
  $headformatI->set_italic();
  $headformatI->set_text_wrap();

  $format     = $workbook->add_format();
  $format->set_align('left');
  $format->set_font('Arial');
  $format->set_text_wrap();

  $formatL     = $workbook->add_format();
  $formatL->set_align('left');
  $formatL->set_font('Arial');
  $formatR    = $workbook->add_format();
  $formatR->set_align('right');
  $formatR->set_font('Arial');
  $formatC    = $workbook->add_format();
  $formatC->set_align('center');
  $formatC->set_font('Arial');
  $formatD    = $workbook->add_format();
  $formatD->set_align('right');
  $formatD->set_font('Arial');
  $formatD->set_num_format('$#,##0.00');	# Money!
  $formatGreen = $workbook->add_format();
  $formatGreen->set_align('left');
  $formatGreen->set_bg_color('lime');
  $formatBlue = $workbook->add_format();
  $formatBlue->set_align('right');
  $formatBlue->set_bg_color('cyan');
  $formatBlueD = $workbook->add_format();
  $formatBlueD->set_align('right');
  $formatBlueD->set_bg_color('cyan');
  $formatBlueD->set_bold;
  $formatBlueD->set_num_format('$#,##0.00');	# Money!

  $formatGreenD = $workbook->add_format();
  $formatGreenD->set_align('right');
  $formatGreenD->set_bg_color('lime');
  $formatGreenD->set_num_format('$#,##0.00');	# Money!
}

#______________________________________________________________________________

sub outPDF {
   my ($format, $out) = @_;

   ($out) = &StripIt_local($out);
   $out = " " if ( !$out );

   if ( $yloc < 30 ) {
      $xloc = $leftmargin;
      $yloc = $ytop - 50;
      $txt->textend;

      $pagenum++;
      $page = $pdf->page(0);
      $page->mediabox('A4');
      $page->cropbox ('A4');
      $txt = $page->text;
      &print_Heading_Line;
      $row  = 0;
      $yloc = $yloc - 16;
   }

   $txt->font( $font{'Times'}{'Roman'}, 10);
   $xlocation = ($row * $colwidth) + 1 + $leftmargin;
   $xlocation += $colwidth/2;

   $txt->translate($xlocation,$yloc);

   if ( $format =~ /L$/i ) {
      $txt->text("$out");
   } elsif ( $format =~ /R$/i ) {
      $txt->text_right("$out");
   } elsif ( $format =~ /C$/i ) {
      $txt->text_center("$out");
   } else {
      $txt->text_right("$out");
   }
}

#______________________________________________________________________________

sub outExcel {
   my ($format, $out) = @_;

   if ( $format || $out ) {
     ($out) = &StripIt_local($out);
     if ( $out =~ /^\s*0\s*$/ ) {
        $out = "0.00";
     } elsif ( !$out ) {
        $out = " ";
     }
     $col = 0 if ( $col =~ /^\s*$/ );
     $row = 0 if ( $row =~ /^\s*$/ );
     if ( $format ) {
       $worksheet->write($row, $col, "$out", $format);
     } else {
       $worksheet->write($row, $col, "$out");
     }
   }
}

#______________________________________________________________________________

sub StripIt_local {
   my ($value) = @_;

   $value =~ s/^\s*(.*?)\s*$/$1/;
   $value =~ s/\/\s+\///g;

   return($value);
}

#______________________________________________________________________________

sub genreport {
  my ($FTYPE, $TS, $CHK) = @_;
  my $my835fn = "";
  my $skip    =  0;

  if ( $FTYPE =~ /^PDF$/i ) {
     $REPORT = "PDF";
     $fname = "${REPORT}_${dispdate2}_${CHKNUM}.pdf";
  } elsif ( $FTYPE =~ /^SS$/i ) {
     $REPORT = "Excel";
     $fname = "${REPORT}_${dispdate2}_${CHKNUM}.xlsx";
  } elsif ( $FTYPE =~ /^835$/i ) {
     if ( $Pharmacy_Wants835Files{$PH_ID} =~ /^Y/i ) {
        $REPORT = "my835";
        $fname = "${REPORT}_${dispdate2}_${CHKNUM}.txt";
     } else {
        $skip++;
     }
  }

  $FILENAME = "$outdir\\$fname";
  $report = "RetrieveRemit";
  $$report = $FILENAME;

  my $my835Filename = "";

  $FILENAME =~ s/\\/\//g;
  my $DateAdded = 0;

  if ( $skip ) {
    print "Skipping! $skip<hr>\n";
  } else {
    if ( $FTYPE =~ /^PDF$/i ) {
       &setPDF($FILENAME);
    } elsif ( $FTYPE =~ /^SS$/i ) {
       &setExcel($FILENAME);
    } elsif ( $FTYPE =~ /^835$/i ) {
       my $NCPDP       = $Pharmacy_NCPDPs{$PH_ID};
       my $ONCPDP      = sprintf("%07d", $NCPDP);
       my $CHECKAMT    = $DISPCHKAMT;
       $CHECKAMT =~ s/^\$|\,//g;

       $ofile = "PAI835_${NCPDP}_${dispdate2}_${CHKNUM}_${CHECKAMT}.out.txt";

       my $ODIR = "D:\\WWW\\members.recon-rx.com\\WebShare\\835s";
       my $useme = 0;

       if ( $ENV =~ /^\s*$|DEV/i ) {
          $my835Filename = "$ODIR\\$PH_ID\\${ofile}";
          $useme++ if ( -e "$my835Filename" );
       }
       if ( !$useme ) {
          $my835Filename = "$ODIR\\$PH_ID\\${ofile}";
       }
    }
    
    my $outline = "";
    if ( $FTYPE =~ /^PDF$|^SS$/i ) {
       &genFile($FTYPE, $REPORT, $fname);
    } else {
       $my835fn = $my835Filename;
#       print "File: $my835fn<br>";
    
       my $jfname = $my835fn;
    
       if ( -d "$jfname" ) {
          my @pcs = split(/\\/, $my835fn);
          $jfname .= "\\" . $pcs[$#pcs];
       }

       if ( !-e "$jfname" ) {
          $outline  = qq##;
          $outline .= qq#jfname:\n$jfname\n\n# if ( $ENV =~ /^\s*$|DEV/i );
          $outline .= qq#835 file is currently not available to be displayed.\nPlease contact ReconRx for assistance.\n\n#;
       } else {
          open(FILE, "< $jfname") || die "Couldn't open input file '$jfname'\n\t$!\n\n";
          while (<FILE>) {
             $outline .= $_;
          }
          close(FILE);
       }
    
       my $outfilename = qq#$outdir/$fname#;
       if ( !-e "$outfilename" && "$outfilename" !~ /.txt/i ) {
            $outfilename .= ".txt";
       }
    
       open(OFILE, "> $outfilename") || die "Couldn't open output file '$outfilename'<br>\n$!<br><br>\n";
       print OFILE "$outline\n";
       close(OFILE);
    }
    
    print qq#<tr><td colspan=3>$REPORT Report for $CHK<br>\n#;
    my $now = time();
    # $URL = qq#http://members.Recon-Rx.com/reports/$fname?TS=$now#;
    #$URL = qq#/reports/$fname?TS=$now#;
     $URL = qq#https://members.Recon-Rx.com/WebShare/reports/$fname?TS=$now#;
    $URL =~ s/ /\%20/g;
    
    print qq#$nbsp <a href="$URL" target=new>$fname</a>#;
    print qq#</td></tr>\n#;
    
    if ( $outline =~ /file not available/i  ) {
       print qq#<tr><td bgcolor="yellow" colspan=3>\n#;
       print qq#jfname: $jfname<br>\n# if ($debug);
       print qq#<br><font color=red size=+1>835 file is currently unavailable to be displayed.<br>\n#;
       print qq#Please <a href="/cgi-bin/Contact_Us.cgi">contact</a> ReconRx for assistance.</font><br><br>\n#;
       print qq#</td></tr>\n#;
    }
  }
}

#______________________________________________________________________________

sub genFile {
   my ($FTYPE, $REPORT, $fname) = @_;

   my $TOTAL_Amount_Billed  = 0;
   my $TOTAL_Amount_CoPayed = 0;
   my $TOTAL_Amount_Payed   = 0;
   my $TOTAL_Claim_Adjustment_Transaction = 0;
   my $TOTAL_Adjustment_Amount = 0;

   my $TAXES            = 0;
   my $TOTAL_TAXES      = 0;
   my $TOTAL_Trans_Fee  = 0;
   my $TOTAL_DIR_FEE    = 0;
   my $TOTAL_TAX_LA_FEE = 0;
   my $TOTAL_LA_FEE     = 0;
   my %ref02            = ();

   if ( $SRC =~ /chklist/i ) {
     $andwhere = "AND b.Payer_ID = $Payer_ID";
   }
   else {
     $andwhere = "AND b.R_TPP_PRI = $TPPPRI";
   }

   my $sql = "SELECT 835remitstbID, R_TS3_NCPDP, R_CLP01_Rx_Number, R_DTM02_Date, R_REF02_Value, R_CLP03_Amount_Billed, R_CLP04_Amount_Payed, R_CLP05_Amount_CoPayed, 
                     R_AMT01_Tax_Amount_Qualifier_Code, R_AMT02_Tax_Amount, R_DIR_Fee, R_Sales_Tax, R_Transaction_Fee
                FROM ( SELECT b.*
                         FROM $P8DBNAME.$check_tbl a
                         JOIN $P8DBNAME.$P8TABLE b ON ( a.Check_ID = b.Check_ID )
                        WHERE a.Pharmacy_ID IN ($PH_ID)
                          AND a.Check_ID = $Check_ID
                          $andwhere
                    UNION ALL
                       SELECT b.*
                         FROM $R8DBNAME.$check_tbl a
                         JOIN $R8DBNAME.$R8TABLE b ON ( a.Check_ID = b.Check_ID )
                        WHERE a.Pharmacy_ID IN ($PH_ID)
                          AND a.Check_ID = $Check_ID
                          $andwhere
                     ) a
            ORDER BY R_DTM02_Date";


   $stb = $dbx->prepare($sql);

   $numofrows = $stb->execute;

   if ( $numofrows <= 0 ) {
     my $jout = "No records found for this Check Number!";
     print "$jout<br>\n";
     if ( $REPORT =~ /Excel/i ) {
        $row = 0;
        $col = 0;
        &outExcel($format , $jout  ); $col++;
     } elsif ( $REPORT =~ /PDF/i ) {
        $row = 0;
        $yloc -= 16;
        &outPDF($format, $jout); $row++;
     }
   } else {
     if ( $REPORT =~ /Excel/i ) {
       $row--;
       &print_Heading_Line;
     }


     while (my @row = $stb->fetchrow_array()) {
       ($Claim_ID, $NCPDP, $R_CLP01_Rx_Number, $R_DTM02_Date, $R_REF02_Value, $Amount_Billed, $Amount_Payed, $Amount_CoPayed, $R_AMT01_Tax_Amount_Qualifier_Code, $R_AMT02_Tax_Amount, $R_DIR_Fee, $R_Sales_Tax, $R_Transaction_Fee) = @row;

       #############################################################################
       # Process CAS entries for DIR Fees first
       #############################################################################

       my $Trans_Fee= 0;
       my $DIR_FEE  = 0;
       my $TAXES    = 0;
       my $TaxLAFee = 0;

       #------------------------------------------------------------------------------
       # Process Trans Fees
       #------------------------------------------------------------------------------

       if ( $Trans_Fee_Loc =~ /^CAS(.*?)130$/ ) {
#          ($Trans_Fee) = &calc_Fee_on_Reason_Code(130);
#          $Trans_Fee = sprintf($FMT, $Trans_Fee) if ( $Trans_Fee != 0);
          $Trans_Fee = sprintf($FMT, $R_Transaction_Fee) if ( $R_Transaction_Fee != 0);
       }

       #------------------------------------------------------------------------------
       #Process DIR Fees
	   
       if ( $DIR_Loc_Display =~ /CAS/i ) {
         my ($dispdir_loc, $dispdir_rsn_cd, $dispdir_rsn_dscr) = split (':', $DIR_Loc_Display);
        
         $dir_sql = "SELECT group_code, reason_code, transaction_amt 
                       FROM $DBNAME.835_cas
                      WHERE claim_id = $Claim_ID
                    ";
         $std = $dbx->prepare($dir_sql);
         $numofrows = $std->execute;
         while (my ($dirgrp,$dirreason,$diramt) = $std->fetchrow_array()) {
           if($dirgrp eq $dispdir_rsn_cd && $dirreason eq $dispdir_rsn_dscr) {
             $DIR_FEE = $diramt;
           }
         }
         $std->finish();
       }

       #---------------------------------------
       # Process Sales Tax

       if ( $R_Sales_Tax ) {
         $TAXES = $R_Sales_Tax;
       }

       #---------------------------------------
       # Process Louisiana Provider Fee

       if ( $LA_Provider_Fee_Loc =~ /^AMT/i ) {
          ($TaxLAFee) = &calc_Fee_on_AMT;
       } elsif ( $LA_Provider_Fee_Loc =~ /^CAS(.*?)105$/i ) {
          ($TaxLAFee) = &calc_Fee_on_Reason_Code($claim_id, 105);
       } elsif ( $LA_Provider_Fee_Loc =~ /^CAS(.*?)137$/i ) {
          ($TaxLAFee) = &calc_Fee_on_Reason_Code($claim_id, 137);
       }

       #---------------------------------------

       my $RxNumber = $R_CLP01_Rx_Number + 0;
       if ( $RxNumber == -1 ) {
          $RxNumber = "Adj Only";
       }

       my $OR_DTM02_Date = substr($R_DTM02_Date, 4, 2) . "/" . substr($R_DTM02_Date, 6, 2). "/" .  substr($R_DTM02_Date, 0, 4);

#-----------------------------------------------------------------------------------------------------
	   
       my $TAX = 0;

       if ( $Tax_Location =~ /^AMT$|^CAS$/i ) {
          $TAX = $TAXES;
       } elsif ( $Tax_Location =~ /^AMT/i ) {
          $dTaxLAFee = $TaxLAFee;
       }

       $DIR_FEE  = sprintf($FMT, $DIR_FEE)  if ( $DIR_FEE  ne "-");
       $TAX      = sprintf($FMT, $TAX)      if ( $TAX      ne "-");
       $TaxLAFee = sprintf($FMT, $TaxLAFee) if ( $TaxLAFee ne "-" );
       $LouisianaFee = sprintf($FMT, $LouisianaFee) if ( $LouisianaFee ne "-");

       $TOTAL_TAXES      += $TAX;
       $TOTAL_DIR_FEE    += $DIR_FEE;
       $TOTAL_Trans_Fee  += $Trans_Fee;
       $TOTAL_TAX_LA_FEE += $TaxLAFee;
       $TOTAL_LA_FEE     += $LouisianaFee;
#-----------------------------------------------------------------------------------------------------
       print "DIR_FEE: $DIR_FEE<br>\n" if ( $DIR_FEE > 0 && $debug );
#-----------------------------------------------------------------------------------------------------

       if ( $REPORT =~ /Excel/i ) {
          $row++;
          $col = 0;
          if ($agg_check) {
            $jout = $NCPDP;        &outExcel($formatC, $jout  ); $col++;
          }
          $jout = $RxNumber;        &outExcel($formatC, $jout  ); $col++;
          $jout = $OR_DTM02_Date;   &outExcel($formatC, $jout  ); $col++;
          $jout = $Amount_Billed;   &outExcel($formatD, $jout  ); $col++;
          $jout = $Amount_CoPayed;  &outExcel($formatD, $jout  ); $col++;
          $jout = $Amount_Payed;    &outExcel($formatD, $jout  ); $col++;
          $jout = $TAX;             &outExcel($formatD, $jout  ); $col++;
          $jout = $Trans_Fee || "-";&outExcel($formatD, $jout  ); $col++;
          $jout = $DIR_FEE || "-";  &outExcel($formatD, $jout  ); $col++;
#         $jout = $dTaxLAFee;       &outExcel($formatD, $jout  ); $col++;
#         $jout = $dLouisianaFee;   &outExcel($formatD, $jout  ); $col++;
       } elsif ( $REPORT =~ /PDF/i ) {
          $row = 0;
          $yloc -= 16;
          if ($agg_check) {
            $jout = $NCPDP;        &outPDF("C", $jout  ); $row++;
          }
          $jout = $RxNumber;        &outPDF("C", $jout  ); $row++;
          $jout = $OR_DTM02_Date;   &outPDF("C", $jout  ); $row++;
          $jout = $Amount_Billed;   &outPDF("D", $jout  ); $row++;
          $jout = $Amount_CoPayed;  &outPDF("D", $jout  ); $row++;
          $jout = $Amount_Payed;    &outPDF("D", $jout  ); $row++;
          $jout = $TAX;             &outPDF("D", $jout  ); $row++;
          $jout = $Trans_Fee || "-";&outPDF("D", $jout  ); $row++;
          $jout = $DIR_FEE || "-";  &outPDF("D", $jout  ); $row++;
#         $jout = $dTaxLAFee;       &outPDF("D", $jout  ); $row++;
#         $jout = $dLouisianaFee;   &outPDF("D", $jout  ); $row++;
       }

       $TOTAL_Amount_Billed     += $Amount_Billed;
       $TOTAL_Amount_CoPayed    += $Amount_CoPayed;
       $TOTAL_Amount_Payed      += $Amount_Payed;

       $ref02{$R_REF02_Value}++;
     }

     my $REF02 = '';

     foreach my $val (keys %ref02) {
       $REF02 .= "$val|";
     }

     chop($REF02);

#     print "REF: $REF02<br>";

#-------------------------------------------------------------------------------------------------------------------------
# Now for Totals!!!!
#-------------------------------------------------------------------------------------------------------------------------
# In this section, process the "PLB" Fee locations for "Fee" fields

   my %PLBS = ();

   if ( $Check_ID ) {
     $plb_sql = "SELECT Adjustment_Reason_Code, Adjustment_Reason_Code_Meaning, Adjustment_Description, SUM(Adjustment_Amount)
                   FROM $P8DBNAME.check_plbs
                  WHERE Check_ID = $Check_ID
               GROUP BY Adjustment_Reason_Code, Adjustment_Reason_Code_Meaning, Adjustment_Description";

#     print "SQL: $plb_sql<br>";
##   print "$plb_sql<br>" if($USER==66);
     $sthp = $dbx->prepare($plb_sql);

     $numofrows = $sthp->execute;

     if ( $numofrows > 0 ) {
       my ($tf_loc, $tf_rsn_cd, $tf_rsn_dscr)    = split (':', $Trans_Fee_Loc_Chk);
       my ($dir_loc, $dir_rsn_cd, $dir_rsn_dscr) = split (':', $DIR_Loc_Chk);
       my $psao = '';

       while (my ($Reason_Code, $Reason_Code_Meaning, $Dscr, $Amount) = $sthp->fetchrow_array()) {
         my $dir_trans_fee = 0;
         next if ( $Dscr !~ /$REF02/i && $TPPPRI =~ /^700470|700929/ );

         if ( $Payer_ID != $TPPPRI && $TPPPRI =~ /^700447/ ) {
           ($p1,$plb) = split("\\[","$Dscr");
           $plb =~ s/\]//g;
           $plb = uc($plb);
           $key="700447##$plb";

           if ( $Lookup_TPP_Display_on_Remit_TPP_IDs{$key} == $Payer_ID ) {
             $PLBS{$Reason_Code_Meaning} += $Amount;
           }
         }
         else {

           if ( ($tf_loc =~ /^PLB/i || $dir_loc =~ /^PLB/i) ) {
             if ( $Reason_Code =~ /$tf_rsn_cd/i && $Dscr =~ /$tf_rsn_dscr/ ) {
               $PLBS{'Transaction Fees'} += $Amount;
               $dir_trans_fee++;
             }
             elsif ( $Reason_Code =~ /$dir_rsn_cd/i && $Dscr =~ /$dir_rsn_dscr/ ) {
               $PLBS{'DIR Fees'} += $Amount;
               $dir_trans_fee++;
             }
             elsif ( $TPPPRI =~ /700447/i && $Dscr =~ /^Total/ ) {
               $PLBS{'DIR Fees'} += $Amount;
               $dir_trans_fee++;
             }
             elsif ( $Reason_Code =~ /$dir_rsn_cd/i && $tf_rsn_dscr =~ /DIR$/i ) {
               $PLBS{'Trans Fees plus DIR Fees ( if applicable)'} += $Amount;
               $dir_trans_fee++;
             }
  
             $PLBS{$Reason_Code_Meaning} += $Amount if ( !$dir_trans_fee );
           }
           else {
             $PLBS{$Reason_Code_Meaning} += $Amount;
           }
         }
       }
     }

     $sthp->finish();
   }

#-----------------------------------------------------------------------------------------------------

     $OTOTAL_Amount_Billed  = "\$" . &commify(sprintf("$FMT", $TOTAL_Amount_Billed));
     $OTOTAL_Amount_CoPayed = "\$" . &commify(sprintf("$FMT", $TOTAL_Amount_CoPayed));
     $OTOTAL_Amount_Payed   = "\$" . &commify(sprintf("$FMT", $TOTAL_Amount_Payed));
     $OTOTAL_TAXES          = "\$" . &commify(sprintf("$FMT", $TOTAL_TAXES));
     $OTOTAL_Trans_Fee      = "\$" . &commify(sprintf("$FMT", $TOTAL_Trans_Fee));
     $OTOTAL_DIR_FEE        = "\$" . &commify(sprintf("$FMT", $TOTAL_DIR_FEE)); ##Took this out because DIR fees for certain TPPs will not display properly(Prime,Caremark,SS&C)
     $OTOTAL_TAX_LA_FEE     = "\$" . &commify(sprintf("$FMT", $TOTAL_TAX_LA_FEE));
     $OTOTAL_LA_FEE         = "\$" . &commify(sprintf("$FMT", $TOTAL_LA_FEE));
#    $OTOTAL_Claim_Adj_Trans= "\$" . &commify(sprintf("$FMT", $TOTAL_Claim_Adjustment_Transaction));
     $OTOTAL_Adj_Amount     = "\$" . &commify(sprintf("$FMT", $TOTAL_Adjustment_Amount));
#     $Check_Amount          = "\$" . &commify(sprintf("$FMT", $R_BPR02_Check_Amount));
     $Check_Amount          = $CHKAMT;

     $TOTAL_Costs  = $TOTAL_Trans_Fee + $TOTAL_Claim_Adjustment_Transaction + $TOTAL_Adjustment_Amount;
     $OTOTAL_Costs = "\$" . &commify(sprintf("$FMT", $TOTAL_Costs));

     if ( $REPORT =~ /Excel/i ) {
        $row++;
        $col = 0;
        $col += 3;
        $col++ if $agg_check;
        $jout = "-"x12;  &outExcel($headformatR, $jout  ); $col++;
        $jout = "-"x12;  &outExcel($headformatR, $jout  ); $col++;
        $jout = "-"x12;  &outExcel($headformatR, $jout  ); $col++;
        $jout = "-"x12;  &outExcel($headformatR, $jout  ); $col++;
        $jout = "-"x12;  &outExcel($headformatR, $jout  ); $col++;
#       $jout = "-"x12;  &outExcel($headformatR, $jout  ); $col++;
#       $jout = "-"x12;  &outExcel($headformatR, $jout  ); $col++;

        $row++;
        $col = 0;
        $col += 3;
        $col++ if $agg_check;
        $jout = "Sub Totals";        &outExcel($headformatR, $jout  ); $col++;
        $jout = $TOTAL_Amount_Payed; &outExcel($headformatD, $jout  ); $col++;
        $jout = $TOTAL_TAXES;        &outExcel($headformatD, $jout  ); $col++;
        $jout = $TOTAL_Trans_Fee;    &outExcel($headformatD, $jout  ); $col++;
        $jout = $TOTAL_DIR_FEE;      &outExcel($headformatD, $jout  ); $col++;
#       $jout = $TOTAL_TAX_LA_FEE;   &outExcel($headformatD, $jout  ); $col++;
#       $jout = $TOTAL_LA_FEE;       &outExcel($headformatD, $jout  ); $col++;

        $row++;
        $col  = 5;
        $col++ if $agg_check;
        $jout = "Fees";  &outExcel($headformat , $jout  ); $col++;
        $saverow = $row;
        $savecol = $col - 2;
        $found = 0;

#-----------------------------------------------------------------------------------------------------

        my $total_plb_amt = 0;

        foreach my $dscr (keys %PLBS) {
           $row++;
           $col = 4;
           $col++ if $agg_check;
           $plb_amt = "\$" . &commify(sprintf("$FMT", -1 * $PLBS{$dscr}));
           $jout = $plb_amt;  &outExcel($headformatD, $jout  ); $col++;
           $jout = "$dscr";
           $col2 = $col++; $worksheet->merge_range( $row, $col, $row, $col2, $jout, $headformatR ); $col++;
           $total_plb_amt += $PLBS{$dscr};
           $found++;
        }

        if ( !$found ) {
           $row = $saverow;
           $col = $savecol;
           $jout = "\$0.00";  &outExcel($headformatD, $jout  ); $col++;
        }

        $row++;
        $col = 4;
        $col++ if $agg_check;
        $jout = "--------";  &outExcel($headformatR, $jout  ); $col++;
        $jout = "--------";  &outExcel($headformat , $jout  ); $col++;

        $row++;
        $col = 4;
        $col++ if $agg_check;

        $jout = $TOTAL_Amount_Payed - $total_plb_amt;
        &outExcel($headformatD, $jout  ); $col++;
        $jout = "Check Amount";  &outExcel($headformat , $jout  ); $col++;

     } elsif ( $REPORT =~ /PDF/i ) {
        $yloc -= 16;
        $row  = 0;
        $row += 3;
        $jout = "-"x12;  &outPDF("R", $jout  ); $row++;
        $jout = "-"x12;  &outPDF("R", $jout  ); $row++;
        $jout = "-"x12;  &outPDF("R", $jout  ); $row++;
        $jout = "-"x12;  &outPDF("R", $jout  ); $row++;
        $jout = "-"x12;  &outPDF("R", $jout  ); $row++;
#        $jout = "-"x12;  &outPDF("R", $jout  ); $row++;
#        $jout = "-"x12;  &outPDF("R", $jout  ); $row++;

        $yloc -= 16;
        $row  = 0;
        $row += 3;
        $jout = "Sub Totals";        &outPDF("R", $jout  ); $row++;
        $jout = $OTOTAL_Amount_Payed;&outPDF("D", $jout  ); $row++;
        $jout = $OTOTAL_TAXES;       &outPDF("D", $jout  ); $row++;
        $jout = $OTOTAL_Trans_Fee;   &outPDF("D", $jout  ); $row++;
        $jout = $OTOTAL_DIR_FEE;     &outPDF("D", $jout  ); $row++;
#        $jout = $OTOTAL_TAX_LA_FEE;  &outPDF("D", $jout  ); $row++;
#        $jout = $OTOTAL_LA_FEE;      &outPDF("D", $jout  ); $row++;

        $yloc -= 16;
        $row  = 5;
        $jout = "Fees";  &outPDF("L" , $jout  ); $row++;
        $saveyloc = $yloc;
        $saverow = $row - 2;
        $found = 0;

#-----------------------------------------------------------------------------------------------------

        my $total_plb_amt = 0;

        foreach my $dscr (keys %PLBS) {
           $row   = 4;
           $yloc -= 16;
           $plb_amt = "\$" . &commify(sprintf("$FMT", -1 * $PLBS{$dscr}));
           $jout = $plb_amt;  &outPDF("D", $jout  ); $row++;
           $jout = $dscr;  &outPDF("L", $jout  ); $row++;
           $total_plb_amt += $PLBS{$dscr};
           $found++;
        }

        $row   = 4;
        $yloc -= 16;
        $jout = "--------";  &outPDF("R", $jout  ); $row++;
        $jout = "--------";  &outPDF("L", $jout  ); $row++;

        $row   = 4;
        $yloc -= 16;

        $jout = "\$" . &commify(sprintf("$FMT", $TOTAL_Amount_Payed - $total_plb_amt) );
        &outPDF("D", $jout  ); $row++;
        $jout = "Check Amount";  &outPDF("L", $jout  ); $row++;

        if ( !$found ) {
           $row  = $saverow;
           $yloc = $savecol;
           $jout = "\$0.00";  &outPDF("D", $jout  ); $row++;
        }
     }
   }

   if ( $REPORT =~ /PDF/i ) {
      $txt->textend;
      $pdf->save;
      $pdf->end( );

   } elsif ( $REPORT =~ /Excel/i ) {

#     &autofit_columns($worksheet);
      $worksheet->set_column("A:A", 11 );
      $worksheet->set_column("B:B", 11 );
      $worksheet->set_column("C:C", 15 );
      $worksheet->set_column("D:D", 15 );
      $worksheet->set_column("E:E", 15 );
      $worksheet->set_column("F:F", 15 );
      $worksheet->set_column("G:G", 11 );
      $worksheet->set_column("H:H", 11 );	# DIR Fee

#     $worksheet->set_column("I:I", 12 );	# Tax & LA Fee
#     $worksheet->set_column("J:J", 12 );	# LA Fee
      $workbook->close();
   }

   $stb->finish;
}

#______________________________________________________________________________

sub print_Heading_Line {
  my $jout = "";

  if ( $REPORT =~ /Excel/i ) {
     $row++;
     $col = 0;
     
     if ($agg_check) {
       $jout = "NCPDP"; &outExcel($headformatC, $jout); $col++;
     }
     $jout = "Rx Num";       &outExcel($headformatC, $jout); $col++;
     $jout = "Fill Date";    &outExcel($headformatC, $jout); $col++;
     $jout = "Amount Billed";&outExcel($headformatR, $jout); $col++;
     $jout = "Amount CoPay"; &outExcel($headformatR, $jout); $col++;
     $jout = "Amount Paid";  &outExcel($headformatR, $jout); $col++;
     $jout = "Tax";          &outExcel($headformatR, $jout); $col++;
     $jout = "Trans Fee";    &outExcel($headformatR, $jout); $col++;
     $jout = "DIR Fee";      &outExcel($headformatR, $jout); $col++;
#    $jout = "Tax & LA Fee"; &outExcel($headformatR, $jout); $col++;
#    $jout = "LA Fee";       &outExcel($headformatR, $jout); $col++;

#    $worksheet->repeat_rows(1);
  } elsif ( $REPORT =~ /PDF/i ) {
     $row  = 0;
     $xloc = $leftmargin;
     if ( $pagenum <= 1 ) {
        $yloc = $ytop - 120;
        print "print_Heading_Line: row: $row, xloc: $xloc, yloc: $yloc<br>\n" if ($debug);

        my $headline_text = $page->text;

        $headline_text->textstart;
#       $headline_text->font($font{'Helvetica'}{'Bold'}, 12);
        $headline_text->font($font{'Times'}{'Roman'}, 12);
        $xlocation = ($row * $colwidth) + 1 + $leftmargin;
#       print "xlocation: $xlocation, yloc: $yloc<br>\n";
        $headline_text->translate($xlocation,$yloc);
        $headline_text->text("$title");
        $headline_text->textend;
        $yloc -= 20;
     }


     $txt = $page->text;
     if ($agg_check) {
       $jout = "NCPDP"; &outPDF("C", $jout); $row++;
     }
     $jout = "Rx Num";    &outPDF("C", $jout); $row++;
     $jout = "Fill Date"; &outPDF("C", $jout); $row++;
     $jout = "Billed";    &outPDF("R", $jout); $row++;
     $jout = "CoPay";     &outPDF("R", $jout); $row++;
     $jout = "Paid";      &outPDF("R", $jout); $row++;
     $jout = "Tax";       &outPDF("R", $jout); $row++;
     $jout = "Trans Fee"; &outPDF("R", $jout); $row++;
     $jout = "DIR Fee";   &outPDF("R", $jout); $row++;
#     $jout = "Tax&LA Fee";&outPDF("R", $jout); $row++;
#     $jout = "LA Fee";    &outPDF("R", $jout); $row++;
  }
}

#_______________________________________________________________________________

sub docmd_local {
  ($cmd) = @_;
  my $out = "";

# print qq#docmd_local: Execute cmd: $cmd\n# if ($debug);
  print qq#Do: $cmd\n# if ($debug);
  chomp($out = `$cmd 2>&1`);
  $cmd = "";
  $out =~ s/
//g;
# print qq#docmd_local: out:\n$out\n# if ($debug && $out);

  return($cmd, $out);
}

#_______________________________________________________________________________

sub calc_Fee_on_Reason_Code {
   my ($claim_id, $Reason_Code) = @_;
   my $Trans_Fee = 0;

   my $sql  = "SELECT SUM(Transaction_Amt) 
                 FROM $DBNAME.835_cas
                WHERE Claim_ID = $claim_id
                  AND Reason_Code = '$Reason_Code'";

   $stf = $dbx->prepare($sql);
   my $numofrows = $stf->execute;

   if ( $numofrows <= 0 ) {
     $Trans_Fee = 0;
   } else {
     while (($Trans_Fee) = $stf->fetchrow_array()) {
     }
   }

   $stf->finish;

   return($Trans_Fee);
}

#_______________________________________________________________________________

sub calc_Fee_on_AMT {
  my $FEE = 0;

  if ( $R_AMT01_Tax_Amount_Qualifier_Code =~ /^T$/i ) {
     $FEE = $R_AMT02_Tax_Amount;
  }
  return ($FEE);
}

#______________________________________________________________________________
